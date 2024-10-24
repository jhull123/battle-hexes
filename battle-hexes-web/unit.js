class Unit {
  #movePath = [];
  #containingHex = undefined;
  #attack;
  #defense;
  #move;
  #movesRemaining;

  constructor(attack, defense, move) {
    this.#attack = attack;
    this.#defense = defense;
    this.#move = move;
    this.#movesRemaining = move;
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

  move(destinationHex) {
    if (this.#movesRemaining <= 0) {
      throw new Error('No movement points remaining!');
    }

    this.setContainingHex(destinationHex);
    this.#movesRemaining--;
  }
}
