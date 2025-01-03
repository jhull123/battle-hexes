import { API_URL } from './battle-api';
import axios from 'axios';

export class Game {
  #id
  #phases
  #currentPhase

  #players
  #currentPlayer

  constructor(id, phases, players) {
    this.#id = id;
    this.#phases = phases;
    this.#currentPhase = phases[0];

    this.#players = players;
    this.#currentPlayer = players[0];
  }

  endPhase() {
    const newPhaseIdx = this.#phases.indexOf(this.#currentPhase) + 1;
    if (newPhaseIdx >= this.#phases.length) {
      this.#currentPhase = this.#phases[0];
      this.#nextPlayer();
      return true;
    } else {
      this.#currentPhase = this.#phases[newPhaseIdx];
      return false;
    }
  }

  #nextPlayer() {
    const newPlayerIdx = this.#players.indexOf(this.#currentPlayer) + 1;
    if (newPlayerIdx >= this.#players.length) {
      this.#currentPlayer = this.#players[0];
    } else {
      this.#currentPlayer = this.#players[newPlayerIdx];
    }
  }

  getId() {
    return this.#id;
  }

  getCurrentPhase() {
    return this.#currentPhase;
  }

  getCurrentPlayer() {
    return this.#currentPlayer;
  }

  getPhases() {
    return this.#phases;
  }

  static async newGameFromServer() {
    const response = await axios.post(`${API_URL}/games`, {});
    return response.data;
  }
}