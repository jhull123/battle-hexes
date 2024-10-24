class Unit {
  #movePath = [];
  #containingHex = undefined;
  #name;
  #type;
  #attack;
  #defense;
  #move;
  #movesRemaining;

  constructor(name, type, attack, defense, move) {
    this.name = name;
    this.type = type;
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

  getMovement() {
    return this.#move;
  }

  getDefense() {
    return this.#defense;
  }

  getAttack() {
    return this.#attack;
  }
}
