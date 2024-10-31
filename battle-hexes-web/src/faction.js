export class Faction {
  #name;
  #counterColor;

  constructor(name, counterColor) {
    this.#name = name;
    this.#counterColor = counterColor;
  }

  getName() {
    return this.#name;
  }

  getCounterColor() {
    return this.#counterColor;
  }
}