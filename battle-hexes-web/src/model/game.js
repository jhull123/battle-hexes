import { battleHexesService } from '../service/service-factory.js';
import { CombatResolver } from './combat-resolver';

export class Game {
  #id
  #phases
  #currentPhase
  #players
  #board
  #combatResolver;
  #scenarioId;
  #playerTypeIds;
  #scores;
  #turnLimit;
  #turnNumber;
  #gameStatus;
  #pendingCombats;
  #reinforcements;
  #gameLog;
  #combatResultsTable;

  constructor(id, phases, players, board, {
    scenarioId = null,
    playerTypeIds = null,
    scores = {},
    turnLimit = null,
    turnNumber = 1,
    gameStatus = null,
    currentPhase = null,
    pendingCombats = null,
    reinforcements = null,
    gameLog = [],
    combatResultsTable,
  } = {}) {
    this.#id = id;
    this.#phases = phases;
    this.#currentPhase = gameStatus?.state === 'completed'
      ? null
      : this.#phaseFromApi(currentPhase) ?? phases[0];
    this.#players = players;
    if (gameStatus?.state === 'completed') {
      this.#players.setCurrentPlayer(null);
    }

    this.#board = board;
    this.#board.players = players;

    this.#combatResolver = new CombatResolver(id, board, { service: battleHexesService });
    this.#scenarioId = typeof scenarioId === 'string' && scenarioId.trim().length > 0
      ? scenarioId
      : null;
    this.#playerTypeIds = Array.isArray(playerTypeIds) && playerTypeIds.every((value) => typeof value === 'string' && value.trim().length > 0)
      ? [...playerTypeIds]
      : null;
    this.#scores = { ...scores };
    this.#turnLimit = Number.isInteger(turnLimit) && turnLimit > 0 ? turnLimit : null;
    this.#turnNumber = Number.isInteger(turnNumber) && turnNumber > 0 ? turnNumber : 1;
    this.#gameStatus = this.#normalizeGameStatus(gameStatus);
    this.#pendingCombats = Array.isArray(pendingCombats) ? [...pendingCombats] : null;
    this.#reinforcements = reinforcements;
    this.#gameLog = gameLog;
    this.#combatResultsTable = combatResultsTable;
    this.#board.setGameplayBlockedProvider?.(() => this.isGameOver());
  }

  endPhase() {
    if (this.isGameOver()) {
      return false;
    }
    const newPhaseIdx = this.#phases.indexOf(this.#currentPhase) + 1;
    if (newPhaseIdx >= this.#phases.length) {
      this.#currentPhase = this.#phases[0];
      const nextPlayer = this.#players.nextPlayer();
      const wrappedToFirstPlayer = nextPlayer === this.#players.getAllPlayers()[0];
      if (wrappedToFirstPlayer) {
        this.#turnNumber += 1;
      }
      this.#board.resetMovesRemaining(nextPlayer);
      this.#board.resetDefensiveFire(nextPlayer);
      return true;
    } else {
      this.#currentPhase = this.#phases[newPhaseIdx];
      if (this.#currentPhase.toLowerCase() === 'combat'
          && !this.hasPendingCombat()) {
        return this.endPhase();
      }
      return false;
    }
  }

  getId() {
    return this.#id;
  }

  getCurrentPhase() {
    return this.#currentPhase;
  }

  getCurrentPlayer() {
    return this.#players.getCurrentPlayer();
  }

  getPhases() {
    return this.#phases;
  }

  getPlayers() {
    return this.#players;
  }

  getBoard() {
    return this.#board;
  }

  getUnitById(unitId) {
    if (typeof unitId !== 'string' || unitId.length === 0) {
      return null;
    }

    for (const unit of this.#board.getUnits()) {
      if (unit.getId() === unitId) {
        return unit;
      }
    }

    return null;
  }

  getFactionForUnitId(unitId) {
    const unit = this.getUnitById(unitId);
    return unit?.getFaction?.() ?? null;
  }

  getScenarioId() {
    return this.#scenarioId;
  }

  getPlayerTypeIds() {
    return this.#playerTypeIds ? [...this.#playerTypeIds] : null;
  }

  getTurnLimit() {
    return this.#turnLimit;
  }

  getTurnNumber() {
    return this.#turnNumber;
  }

  getScores() {
    return { ...this.#scores };
  }

  getReinforcements() {
    return this.#reinforcements;
  }

  getGameLog() {
    return this.#gameLog;
  }

  getCombatResultsTable() {
    return this.#combatResultsTable;
  }

  updateScores(scores = {}) {
    if (!scores || typeof scores !== 'object') {
      this.#scores = {};
      return;
    }

    const entries = Object.entries(scores).map(([playerName, value]) => {
      const safeValue = Number.isFinite(value) ? value : 0;
      return [playerName, safeValue];
    });

    this.#scores = Object.fromEntries(entries);
  }

  updateTurnState({ turnLimit = this.#turnLimit, turnNumber = this.#turnNumber } = {}) {
    this.#turnLimit = Number.isInteger(turnLimit) && turnLimit > 0 ? turnLimit : null;
    this.#turnNumber = Number.isInteger(turnNumber) && turnNumber > 0 ? turnNumber : 1;
  }

  getGameStatus() {
    return this.#gameStatus ? { ...this.#gameStatus } : null;
  }

  updateGameStatus(gameStatus) {
    this.#gameStatus = this.#normalizeGameStatus(gameStatus);
  }

  applyApiState(responseData = {}) {
    const state = responseData?.game ?? responseData?.sparseBoard ?? responseData;
    const gameStatus = this.#extractGameStatus(responseData);
    if (gameStatus !== undefined) {
      this.updateGameStatus(gameStatus);
    }
    if (this.isGameOver()) {
      this.#currentPhase = null;
      this.#players.setCurrentPlayer(null);
      this.#pendingCombats = [];
    }
    if (Object.prototype.hasOwnProperty.call(state ?? {}, 'currentPhase')) {
      this.#currentPhase = state.currentPhase === null
        ? null
        : this.#phaseFromApi(state.currentPhase) ?? this.#currentPhase;
    }
    if (Object.prototype.hasOwnProperty.call(state ?? {}, 'activePlayer')) {
      const previousPlayer = this.#players.getCurrentPlayer();
      this.#players.setCurrentPlayer(state.activePlayer);
      const activePlayer = this.#players.getCurrentPlayer();
      if (activePlayer && activePlayer !== previousPlayer) {
        this.#board.resetMovesRemaining(activePlayer);
      }
    }
    if (Object.prototype.hasOwnProperty.call(state ?? {}, 'pendingCombats')) {
      this.#pendingCombats = Array.isArray(state.pendingCombats)
        ? [...state.pendingCombats]
        : [];
    }
    if (Object.prototype.hasOwnProperty.call(state ?? {}, 'reinforcements')) {
      this.#reinforcements = state.reinforcements;
    }
    if (Object.prototype.hasOwnProperty.call(state ?? {}, 'gameLog')) {
      this.#gameLog = state.gameLog;
    }
    if (Object.prototype.hasOwnProperty.call(state ?? {}, 'combatResultsTable')) {
      this.#combatResultsTable = state.combatResultsTable;
    }
    if (Object.prototype.hasOwnProperty.call(responseData ?? {}, 'scores')) {
      this.updateScores(responseData.scores);
    }
    if (Object.prototype.hasOwnProperty.call(state ?? {}, 'turnLimit')
        || Object.prototype.hasOwnProperty.call(state ?? {}, 'turnNumber')) {
      this.updateTurnState({
        turnLimit: state?.turnLimit,
        turnNumber: state?.turnNumber,
      });
    }
  }

  hasPendingCombat() {
    return this.#pendingCombats === null
      ? this.#board.hasCombat()
      : this.#pendingCombats.length > 0;
  }

  #phaseFromApi(phase) {
    if (typeof phase !== 'string') {
      return null;
    }
    const normalized = phase.replaceAll('_', ' ').toLowerCase();
    return this.#phases.find(
      (candidate) => candidate.toLowerCase() === normalized,
    ) ?? null;
  }

  isGameOver() {
    return this.#gameStatus?.state === 'completed';
  }

  #extractGameStatus(responseData) {
    if (Object.prototype.hasOwnProperty.call(responseData ?? {}, 'gameStatus')) {
      return responseData.gameStatus;
    }
    if (Object.prototype.hasOwnProperty.call(responseData?.sparseBoard ?? {}, 'gameStatus')) {
      return responseData.sparseBoard.gameStatus;
    }
    return undefined;
  }

  #normalizeGameStatus(gameStatus) {
    if (!gameStatus || typeof gameStatus !== 'object') {
      return null;
    }
    return { ...gameStatus };
  }

  resolveCombat(finishedCb) {
    return this.#combatResolver.resolveCombat().then((combatResult) => {
      this.applyApiState(combatResult);
      if (finishedCb) {
        finishedCb(combatResult);
      }
      return combatResult;
    });
  }
  
  static async newGameFromServer({
    scenarioId = 'elim_1',
    playerTypes = ['human', 'random'],
    service = battleHexesService,
  } = {}) {
    return service.createGame({ scenarioId, playerTypes });
  }

  static async fetchGameFromServer(gameId, { service = battleHexesService } = {}) {
    return service.getGame(gameId);
  }
}
