import { Game } from './game.js';

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
  const pathMatch = window.location.pathname.match(/battle(?:\.html)?\/([^/?#]+)/);
  if (pathMatch && pathMatch[1]) {
    return pathMatch[1];
  }

  const params = new URLSearchParams(window.location.search);
  return params.get('gameId');
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

export const loadGameData = async () => {
  const existingGameId = extractGameIdFromLocation();
  if (existingGameId) {
    const gameData = await Game.fetchGameFromServer(existingGameId);
    updateUrlWithGameId(gameData.id);
    rememberLoadedGameData(gameData);
    return gameData;
  }

  const defaultGame = await Game.newGameFromServer();
  updateUrlWithGameId(defaultGame.id);
  rememberLoadedGameData(defaultGame);
  return defaultGame;
};
