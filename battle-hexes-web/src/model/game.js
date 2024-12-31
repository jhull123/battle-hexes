export class Game {
  #phases
  #currentPhase

  #players
  #currentPlayer

  constructor(phases, players) {
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
    } else {
      this.#currentPhase = this.#phases[newPhaseIdx]; 
    }
  }

  #nextPlayer() {
    const newPlayerIdx = this.#players.indexOf(this.#players) + 1;
    if (newPlayerIdx >= this.#players.length) {
      this.#currentPlayer = this.#players[0];
    } else {
      this.#currentPlayer = this.#players[newPlayerIdx];
    }
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
}