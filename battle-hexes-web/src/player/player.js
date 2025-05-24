export class Player {
  #name;
  #type;
  #factions;

  constructor(name, type, factions) {
    this.#name = name;
    this.#type = type;
    this.#factions = factions;
    if (this.#factions) {
      this.#factions.forEach(faction => faction.setOwningPlayer(this));
    }
  }

  getName() {
    return this.#name;
  }

  getType() {
    return this.#type;
  }

  isHuman() {
    return this.#type === playerTypes.HUMAN;
  }

  getFactions() {
    return this.#factions;
  }
}

export class CpuPlayer extends Player {
  constructor(name, factions) {
    super(name, playerTypes.CPU, factions);
  }

  makeMove() {
    // TODO Implement CPU logic to make a move based on the game state
    console.log(`${this.getName()} is making a move.`);
  }
}

export class Players {
  #players;
  #currentPlayer;

  constructor(players) {
    this.#players = players;
    if (players) {
      this.#currentPlayer = players[0];
    } else {
      throw new Error('Players cannot be null or undefined.');
    }
  }

  getCurrentPlayer() {
    return this.#currentPlayer;
  }

  nextPlayer() {
    const newPlayerIdx = this.#players.indexOf(this.#currentPlayer) + 1;
    if (newPlayerIdx >= this.#players.length) {
      this.#currentPlayer = this.#players[0];
    } else {
      this.#currentPlayer = this.#players[newPlayerIdx];
    }
    return this.#currentPlayer;
  }

  getAllPlayers() {
    return this.#players;
  }
}

export const playerTypes = {
  HUMAN: 'Human',
  CPU: 'Computer'
};
