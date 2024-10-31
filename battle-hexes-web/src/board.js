import { Hex } from './hex.js';

export class Board {
  #factions;
  #hexMap;
  #selectedHex;
  #hoverHex;
  #units;
  #factionTurn; // the faction whose turn it is

  constructor(rows, columns, factions) {
    this.#factions = factions;
    this.#factionTurn = factions[0];

    this.#hexMap = new Map();
    this.#units = new Set();

    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        this.#hexMap.set(`${row},${column}`, new Hex(row, column));
      }
    }
  }

  endTurn() {
    this.resetMovesRemaining();
    let nextFactionIdx = this.#factions.indexOf(this.#factionTurn) + 1
    nextFactionIdx = nextFactionIdx < this.#factions.length ? nextFactionIdx : 0;
    return this.#factionTurn = this.#factions[nextFactionIdx];
  }

  addUnit(unit, row, column) {
    this.#units.add(unit);
    if (row !== undefined && column !== undefined) {
      this.getHex(row, column).addUnit(unit);
    }
  }

  getUnits() {
    return this.#units;
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
    
    const oldSelection = this.#selectedHex;

    if (!oldSelection) {
      // nothing
    } else if (!oldSelection.isEmpty() && oldSelection.isAdjacent(hexToSelect)
        && oldSelection.getUnits()[0].getMovesRemaining() > 0) {
      const units = oldSelection.getUnits();
      console.log(`Moving unit ${units[0]}.`);
      this.moveUnit(units[0], oldSelection, hexToSelect);
      // units[0].addToMovePath(oldSelection);
      // units[0].addToMovePath(hexToSelect);
      oldSelection.setSelected(false);
      hexToSelect.setSelected(true);
      this.setHoverHex(undefined);
    } else {
      oldSelection.setSelected(false);
    }

    this.#selectedHex = hexToSelect;
    if (hexToSelect) this.#selectedHex.setSelected(true);
    
    return oldSelection;
  }

  moveUnit(unit, oldHex, newHex) {
    unit.move(newHex);
    oldHex.removeUnit(unit);
    newHex.addUnit(unit);
  }

  hasSelection() {
    return this.#selectedHex !== undefined;
  }

  setHoverHex(hoverHex) {
    const oldHover = this.#hoverHex;
    this.#hoverHex = hoverHex;

    if (oldHover === this.#hoverHex) {
      return oldHover;
    }

    if (this.#hoverHex && this.hasSelection() && !this.#selectedHex.isEmpty()
        && !this.#selectedHex.hasUnitMoves() 
        && this.#hoverHex.isAdjacent(this.#selectedHex)) {
      // console.log(`We have a move hover hex! ${this.#hoverHex}`);
      this.#hoverHex.setMoveHoverFromHex(this.getSelectedHex());
    }

    if (oldHover) {
      oldHover.setMoveHoverFromHex(undefined);
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
      let aHex = this.getHexStrCoord(hexCoords);
      if (aHex) {
        hexSet.add(aHex);
      }
    }

    return hexSet;
  }

  getHexNeighborhoods(someHexes) {
    let allTheHexes = new Set();
  
    for (let targetHex of someHexes) {
      this.getHexAndAdjacent(targetHex).forEach(neighborHex => allTheHexes.add(neighborHex));
    }

    return allTheHexes;
  }

  getSelectedHex() {
    return this.#selectedHex;
  }

  resetMovesRemaining() {
    for (let unit of this.#units) {
      unit.resetMovesRemaining();
    }
  }
}
