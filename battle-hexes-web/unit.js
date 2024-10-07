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
    this.#movePath.add(hexToMoveTo);
  }
}
