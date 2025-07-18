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

  constructor(id, phases, players, board) {
    this.#id = id;
    this.#phases = phases;
    this.#currentPhase = phases[0];
    this.#players = players;

    this.#board = board;
    this.#board.setPlayers(players);

    this.#combatResolver = new CombatResolver(id, board);
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
  
  static async newGameFromServer() {
    const response = await axios.post(`${API_URL}/games`, {});
    return response.data;
  }
}
