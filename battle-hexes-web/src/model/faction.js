export class Faction {
  #name;
  #counterColor;
  #owningPlayer;

  constructor(name, counterColor) {
    this.#name = name;
    this.#counterColor = counterColor;
  }

  setOwningPlayer(player) {
    this.#owningPlayer = player;
  }

  getName() {
    return this.#name;
  }

  getCounterColor() {
    return this.#counterColor;
  }

  getOwningPlayer() {
    return this.#owningPlayer;
  }

  toString() {
    return this.#name;
  }
}
