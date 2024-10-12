class Hex {
  #units;
  #adjacentHexCoords;
  #selected;
  #moveHover;

  constructor(row, column) {
    this.row = row;
    this.column = column;
    this.#units = [];
    this.#selected = false;
    this.#moveHover = false;

    if (column % 2 === 0) {
      this.#adjacentHexCoords = new Set([
        `${row - 1},${column}`,
        `${row - 1},${column + 1}`,
        `${row},${column + 1}`,
        `${row + 1},${column}`,
        `${row},${column - 1}`,
        `${row - 1},${column - 1}`
      ]);
    } else {
      this.#adjacentHexCoords = new Set([
        `${row - 1},${column}`,
        `${row},${column + 1}`,
        `${row + 1},${column + 1}`,
        `${row + 1},${column}`,
        `${row + 1},${column - 1}`,
        `${row},${column - 1}`
      ]);
    }
  }

  addUnit(unit) {
    this.#units.push(unit);
  }

  getUnits() {
    return this.#units;
  }

  isEmpty() {
    return this.#units.length == 0;
  }

  coordsHumanString() {
    return `${this.row}, ${this.column}`
  }

  isAdjacent(anotherHex) {
    if (anotherHex === undefined || anotherHex === this) return false;
    return this.#adjacentHexCoords.has(`${anotherHex.row},${anotherHex.column}`);
  }

  getAdjacentHexCoords() {
    return this.#adjacentHexCoords;
  }

  isSelected() {
    return this.#selected;
  }

  setSelected(select) {
    this.#selected = select;
  }

  setMoveHover(moveHover) {
    this.#moveHover = moveHover;
  }

  isMoveHover() {
    return this.#moveHover;
  }
}
