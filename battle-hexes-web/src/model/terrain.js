export class Terrain {
  #name;
  #color;

  constructor(name, color) {
    this.#name = name;
    this.#color = color;
  }

  getName() {
    return this.#name;
  }

  getColor() {
    return this.#color;
  }
}
