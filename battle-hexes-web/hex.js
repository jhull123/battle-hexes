class Hex {
  #units;
  #adjacentHexCoords;

  constructor(row, column) {
    this.row = row;
    this.column = column;
    this.units = [];
    if (column % 2 === 0) {
      this.adjacentHexCoords = new Set([
        `${row - 1},${column}`,
        `${row - 1},${column + 1}`,
        `${row},${column + 1}`,
        `${row + 1},${column}`,
        `${row},${column - 1}`,
        `${row - 1},${column - 1}`
      ]);
    } else {
      this.adjacentHexCoords = new Set([
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
    this.units.push(unit);
  }

  getUnits() {
    return units;
  }

  isEmpty() {
    return this.units.length == 0;
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
    return this.adjacentHexCoords;
  }
}
