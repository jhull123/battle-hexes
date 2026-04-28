import { Game } from './game.js';
import { battleHexesService } from '../service/service-factory.js';

const DEFAULT_SCENARIO_ID = 'elim_1';
const DEFAULT_PLAYER_TYPES = ['human', 'random'];

let lastLoadedConfig = {
  scenarioId: DEFAULT_SCENARIO_ID,
  playerTypes: [...DEFAULT_PLAYER_TYPES],
};

const cloneConfig = (config) => ({
  scenarioId: config?.scenarioId ?? DEFAULT_SCENARIO_ID,
  playerTypes: [...(config?.playerTypes ?? DEFAULT_PLAYER_TYPES)],
});

const isStringArray = (value) =>
  Array.isArray(value)
  && value.length > 0
  && value.every((item) => typeof item === 'string' && item.trim().length > 0);

const readNestedValue = (source, path) =>
  path.reduce((value, key) => (value && value[key] !== undefined ? value[key] : undefined), source);

const derivePlayerTypesFromPlayers = (players) => {
  if (!Array.isArray(players) || players.length === 0) {
    return null;
  }

  const candidatePaths = [
    ['typeId'],
    ['type_id'],
    ['playerTypeId'],
    ['player_type_id'],
    ['metadata', 'typeId'],
    ['metadata', 'type_id'],
    ['controller', 'id'],
    ['controller', 'typeId'],
    ['controller', 'type_id'],
  ];

  const candidateTypes = players.map((player) => {
    for (const path of candidatePaths) {
      const value = readNestedValue(player, path);
      if (typeof value === 'string' && value.trim().length > 0) {
        return value;
      }
    }
    return null;
  });

  if (candidateTypes.every((typeId) => typeof typeId === 'string' && typeId.trim().length > 0)) {
    return candidateTypes;
  }

  return null;
};

const derivePlayerTypes = (gameData) => {
  if (!gameData || typeof gameData !== 'object') {
    return null;
  }

  const topLevelCandidates = [
    gameData.playerTypeIds,
    gameData.playerTypes,
    gameData.player_type_ids,
    gameData.player_types,
  ];

  for (const candidate of topLevelCandidates) {
    if (isStringArray(candidate)) {
      return [...candidate];
    }
  }

  const fromPlayers = derivePlayerTypesFromPlayers(gameData.players);
  if (isStringArray(fromPlayers)) {
    return [...fromPlayers];
  }

  return null;
};

const updateLastLoadedConfig = (gameData) => {
  const scenarioId = gameData?.scenarioId
    ?? lastLoadedConfig?.scenarioId
    ?? DEFAULT_SCENARIO_ID;
  const derivedPlayerTypes = derivePlayerTypes(gameData)
    ?? lastLoadedConfig?.playerTypes
    ?? DEFAULT_PLAYER_TYPES;

  lastLoadedConfig = {
    scenarioId,
    playerTypes: [...derivedPlayerTypes],
  };

  return cloneConfig(lastLoadedConfig);
};

export const getLastLoadedConfig = () => cloneConfig(lastLoadedConfig);

export const rememberLoadedGameData = (gameData) => updateLastLoadedConfig(gameData);

export const extractGameIdFromLocation = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get("gameId");
};

export const updateUrlWithGameId = (gameId) => {
  const params = new URLSearchParams(window.location.search);
  params.set('gameId', gameId);
  const query = params.toString();
  let pathname = window.location.pathname;

  if (/battle(?:\.html)?\/[^/]+$/.test(pathname)) {
    pathname = pathname.replace(/(battle(?:\.html)?\/)[^/]+$/, `$1${encodeURIComponent(gameId)}`);
  }

  const canReplace =
    window.location.protocol === 'http:' || window.location.protocol === 'https:';

  if (canReplace && 'replaceState' in history) {
    history.replaceState(null, '', `${pathname}${query ? `?${query}` : ''}`);
  }
};

const extractScenarioId = (gameData) => {
  const scenarioId = gameData?.scenarioId ?? gameData?.scenario_id ?? null;
  return typeof scenarioId === 'string' && scenarioId.trim().length > 0
    ? scenarioId
    : null;
};

const extractStackingLimit = (scenario) => {
  const candidates = [
    scenario?.stackingLimit,
    scenario?.stacking_limit,
  ];

  for (const candidate of candidates) {
    if (Number.isInteger(candidate) && candidate > 0) {
      return candidate;
    }
  }

  return null;
};

export const hydrateGameDataWithScenarioMetadata = async (
  gameData,
  { service = battleHexesService } = {},
) => {
  if (!gameData || typeof gameData !== 'object') {
    return gameData;
  }

  const hasStackingLimit =
    (Number.isInteger(gameData.stackingLimit) && gameData.stackingLimit > 0)
    || (Number.isInteger(gameData.stacking_limit) && gameData.stacking_limit > 0);
  if (hasStackingLimit) {
    return gameData;
  }

  const scenarioId = extractScenarioId(gameData);
  if (!scenarioId) {
    return gameData;
  }

  let scenarios;
  try {
    scenarios = await service.listScenarios();
  } catch (error) {
    console.warn('Failed to load scenario metadata for game data hydration.', error);
    return gameData;
  }

  const scenario = Array.isArray(scenarios)
    ? scenarios.find((candidate) => candidate?.id === scenarioId)
    : null;
  const stackingLimit = extractStackingLimit(scenario);
  if (!stackingLimit) {
    return gameData;
  }

  return {
    ...gameData,
    stackingLimit,
  };
};

export const loadGameData = async () => {
  const existingGameId = extractGameIdFromLocation();
  if (existingGameId) {
    const gameData = await Game.fetchGameFromServer(existingGameId);
    const hydratedGameData = await hydrateGameDataWithScenarioMetadata(gameData);
    updateUrlWithGameId(hydratedGameData.id);
    rememberLoadedGameData(hydratedGameData);
    return hydratedGameData;
  }

  const defaultGame = await Game.newGameFromServer();
  const hydratedDefaultGame = await hydrateGameDataWithScenarioMetadata(defaultGame);
  updateUrlWithGameId(hydratedDefaultGame.id);
  rememberLoadedGameData(hydratedDefaultGame);
  return hydratedDefaultGame;
};
