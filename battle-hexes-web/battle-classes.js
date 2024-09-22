class Hex {
  #units;

  constructor(row, column) {
  	this.row = row;
  	this.column = column;
  	this.units = [];
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
}

class Unit {
  constructor() {
  }
}

class Board {
  #hexMap;
  #selectedHex;

  constructor(rows, columns) {
    this.hexMap = new Map();

    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        this.hexMap.set(`${row},${column}`, new Hex(row, column));
      }
    }
  }

  getHex(row, column) {
    return this.hexMap.get(`${row},${column}`);
  }

  getAllHexes() {
    return this.hexMap.values();
  }

  select(hexToSelect) {
  	this.selectedHex = hexToSelect;
  }

  deselect() {
  	let oldSelection = this.selectedHex;
  	this.selectedHex = undefined;
  	return oldSelection;
  }

  isSelected(aHex) {
  	return aHex !== undefined && this.selectedHex === aHex;
  }

  hasSelection() {
    return this.selectedHex !== undefined;
  }
}