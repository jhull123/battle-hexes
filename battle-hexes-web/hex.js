class Hex {
  #units;
  #adjacentHexCoords;
  #selected;
  #moveTarget;

  constructor(row, column) {
    this.row = row;
    this.column = column;
    this.#units = [];
    this.#selected = false;
    this.#moveTarget = false;

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
    return this.adjacentHexCoords.has(`${anotherHex.row},${anotherHex.column}`);
  }

  isAdjacent_old(anotherHex) {
    if (anotherHex === undefined || anotherHex === this) return false;

    let rowDiff = anotherHex.row - this.row;
    if (rowDiff > 1 || rowDiff < -1) return false;

    let colDiff = anotherHex.column - this.column;

    switch (rowDiff) {
      case 1:
        return Math.abs(colDiff) < 2;
      case 0:
        return Math.abs(colDiff) === 1;
      case -1:
        return colDiff === 0;
    }

    return false;
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

  isMoveTarget() {
    return this.#moveTarget;
  }

  setMoveTarget(moveTarget) {
    this.#moveTarget = moveTarget;
  }
}
