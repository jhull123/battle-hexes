class Unit {
  #movePath = [];
  #containingHex = undefined;

  constructor() {
  }

  getContainingHex() {
    return this.#containingHex;
  }

  setContainingHex(aHex) {
    this.#containingHex = aHex;
  }

  addToMovePath(hexToMoveTo) {
    this.#movePath.push(hexToMoveTo);
  }

  getMovePath() {
    return this.#movePath;
  }

  hasMovePath() {
    return this.#movePath.length > 0;
  }
}
