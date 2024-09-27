class Hex {
  #units;
  #adjacentHexCoords;

  constructor(row, column) {
  	this.row = row;
  	this.column = column;
  	this.units = [];
    if (column % 2 === 0) {
      this.adjacentHexCoords = new Set([
        `${row - 1},${column    }`,
        `${row - 1},${column + 1}`,
        `${row    },${column + 1}`,
        `${row + 1},${column    }`,
        `${row    },${column - 1}`,
        `${row - 1},${column - 1}`
      ]);
    } else {
      this.adjacentHexCoords = new Set([
        `${row - 1},${column    }`,
        `${row    },${column + 1}`,
        `${row + 1},${column + 1}`,
        `${row + 1},${column    }`,
        `${row + 1},${column - 1}`,
        `${row    },${column - 1}`
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

class Unit {
  constructor() {
  }
}

class Board {
  #hexMap;
  #selectedHex;
  #moveHoverHex;

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

  getHexStrCoord(strCoord) {
    return this.hexMap.get(strCoord);
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

  setMoveHoverHex(hoverHex) {
    this.moveHoverHex = hoverHex;
  }

  dehover() {
    let oldHover = this.moveHoverHex;
    this.moveHoverHex = undefined;
    return oldHover;
  }

  isHovered(aHex) {
    return aHex !== undefined && this.moveHoverHex === aHex;
  }
}