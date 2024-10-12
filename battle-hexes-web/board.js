class Board {
  #hexMap;
  #selectedHex;
  #hoverHex;

  constructor(rows, columns) {
    this.#hexMap = new Map();

    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        this.#hexMap.set(`${row},${column}`, new Hex(row, column));
      }
    }
  }

  getHex(row, column) {
    return this.#hexMap.get(`${row},${column}`);
  }

  getHexStrCoord(strCoord) {
    return this.#hexMap.get(strCoord);
  }

  getAllHexes() {
    return this.#hexMap.values();
  }

  selectHex(hexToSelect) {
      if (hexToSelect === this.#selectedHex) return;
      
      let oldSelection = this.#selectedHex;
      if (oldSelection) oldSelection.setSelected(false);

      this.#selectedHex = hexToSelect;
      if (hexToSelect) this.#selectedHex.setSelected(true);
      
      return oldSelection;
  }

  hasSelection() {
    return this.#selectedHex !== undefined;
  }

  setHoverHex(hoverHex) {
    let oldHover = this.#hoverHex;
    this.#hoverHex = hoverHex;

    if (oldHover === this.#hoverHex) {
      return oldHover;
    }

    if (this.#hoverHex && this.hasSelection() && !this.#hoverHex.isEmpty() 
        && this.#hoverHex.isAdjacent(this.#selectedHex)) {
      this.#hoverHex.setMoveHover(true);
    }

    if (oldHover) {
      oldHover.setMoveHover(false);
    }

    return oldHover;
  }

  getHexAndAdjacent(aHex) {
    const hexSet = new Set();

    if (aHex === undefined) {
      return hexSet;
    }

    hexSet.add(aHex);

    for (let hexCoords of aHex.getAdjacentHexCoords()) {
      let aHex = board.getHexStrCoord(hexCoords);
      if (aHex) {
        hexSet.add(aHex);
      }
    }

    return hexSet;
  }

  getHexNeighborhoods(someHexes) {
    let allTheHexes = new Set();
  
    for (let targetHex of someHexes) {
      board.getHexAndAdjacent(targetHex).forEach(neighborHex => allTheHexes.add(neighborHex));
    }

    return allTheHexes;
  }  
}