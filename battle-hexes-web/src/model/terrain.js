export class Terrain {
  #name;
  #color;
  #moveCost;

  constructor(name, color, moveCost = 1) {
    this.#name = name;
    this.#color = color;
    this.#moveCost = Number.isFinite(moveCost) && moveCost > 0 ? moveCost : 1;
  }

  get name() {
    return this.#name;
  }

  get color() {
    return this.#color;
  }

  get moveCost() {
    return this.#moveCost;
  }
}
