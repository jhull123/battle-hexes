export class Faction {
  #name;
  #counterColor;
  #playerType;

  constructor(name, counterColor, playerType) {
    this.#name = name;
    this.#counterColor = counterColor;
    this.#playerType = playerType;
  }

  getName() {
    return this.#name;
  }

  getCounterColor() {
    return this.#counterColor;
  }

  getPlayerType() {
    return this.#playerType;
  }

  toString() {
    return this.#name;
  }
}

export const playerTypes = {
  HUMAN: 'Human',
  CPU: 'Computer'
};