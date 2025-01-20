export class Faction {
  #id;
  #name;
  #counterColor;
  #owningPlayer;

  constructor(id, name, counterColor) {
    this.#id = id;
    this.#name = name;
    this.#counterColor = counterColor;
  }

  setOwningPlayer(player) {
    this.#owningPlayer = player;
  }

  getId() {
    return this.#id;
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
