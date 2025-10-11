import { API_URL } from './battle-api';
import axios from 'axios';
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

  constructor(id, phases, players, board, {
    scenarioId = null,
    playerTypeIds = null,
  } = {}) {
    this.#id = id;
    this.#phases = phases;
    this.#currentPhase = phases[0];
    this.#players = players;

    this.#board = board;
    this.#board.setPlayers(players);

    this.#combatResolver = new CombatResolver(id, board);
    this.#scenarioId = typeof scenarioId === 'string' && scenarioId.trim().length > 0
      ? scenarioId
      : null;
    this.#playerTypeIds = Array.isArray(playerTypeIds) && playerTypeIds.every((value) => typeof value === 'string' && value.trim().length > 0)
      ? [...playerTypeIds]
      : null;
  }

  endPhase() {
    const newPhaseIdx = this.#phases.indexOf(this.#currentPhase) + 1;
    if (newPhaseIdx >= this.#phases.length) {
      this.#currentPhase = this.#phases[0];
      this.#players.nextPlayer();
      this.#board.resetMovesRemaining();
      return true;
    } else {
      this.#currentPhase = this.#phases[newPhaseIdx];
      if (this.#currentPhase.toLowerCase() === 'combat'
          && !this.#board.hasCombat()) {
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

  getScenarioId() {
    return this.#scenarioId;
  }

  getPlayerTypeIds() {
    return this.#playerTypeIds ? [...this.#playerTypeIds] : null;
  }

  isGameOver() {
    const owners = new Set();
    for (const unit of this.#board.getUnits()) {
      if (unit.getContainingHex()) {
        owners.add(unit.getOwningPlayer());
      }
    }
    return owners.size <= 1;
  }

  resolveCombat(finishedCb) {
    return this.#combatResolver.resolveCombat().then(() => {
      if (finishedCb) {
        finishedCb();
      }
    });
  }
  
  static async newGameFromServer({
    scenarioId = 'elem_1',
    playerTypes = ['human', 'random'],
  } = {}) {
    const response = await axios.post(`${API_URL}/games`, {
      scenarioId,
      playerTypes,
    });
    return response.data;
  }

  static async fetchGameFromServer(gameId) {
    const response = await axios.get(`${API_URL}/games/${gameId}`);
    return response.data;
  }
}
