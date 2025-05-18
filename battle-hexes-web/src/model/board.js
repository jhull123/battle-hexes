import { Hex } from './hex.js';

export class Board {
  #hexMap;
  #selectedHex;
  #hoverHex;
  #units;
  #players;

  constructor(rows, columns) {
    this.#hexMap = new Map();
    this.#units = new Set();

    for (let row = 0; row < rows; row++) {
      for (let column = 0; column < columns; column++) {
        this.#hexMap.set(`${row},${column}`, new Hex(row, column));
      }
    }
  }

  setPlayers(players) {
    this.#players = players;
  }

  addUnit(unit, row, column) {
    this.#units.add(unit);
    if (row !== undefined && column !== undefined) {
      const targetHex = this.getHex(row, column);
      targetHex.addUnit(unit);
      unit.setContainingHex(targetHex);
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
    } else if (this.isOppositionHex(oldSelection)) {
      oldSelection.setSelected(false);
    } else if (!oldSelection.isEmpty() && oldSelection.isAdjacent(hexToSelect)
        && oldSelection.getUnits()[0].isMovable() && !this.isOppositionHex(hexToSelect)) {
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
    unit.move(newHex, this.getAdjacentHexes(newHex));
    oldHex.removeUnit(unit);
    newHex.addUnit(unit);
  }

  updateUnitPosition(unit, oldHex, newHex) {
    if (oldHex === newHex) {
      return;
    }
    if (oldHex !== undefined && oldHex !== null) {
      oldHex.removeUnit(unit);
    }
    if (newHex !== undefined && newHex !== null) {
      newHex.addUnit(unit);
    }
    unit.setContainingHex(newHex);
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
        && this.#hoverHex.isAdjacent(this.#selectedHex)
        && this.isOwnHexSelected()
        && !this.isOppositionHex(hoverHex)) {
      console.log(`We have a move hover hex! ${this.#hoverHex}`);
      this.#hoverHex.setMoveHoverFromHex(this.getSelectedHex());
    }

    if (oldHover) {
      oldHover.setMoveHoverFromHex(undefined);
    }

    return oldHover;
  }

  getHexAndAdjacent(aHex) {
    if (aHex === undefined || aHex === null) {
      return new Set();
    }

    const hexSet = this.getAdjacentHexes(aHex);
    hexSet.add(aHex);
    return hexSet;
  }

  getAdjacentHexes(aHex) {
    const hexSet = new Set();

    for (let hexCoords of aHex.getAdjacentHexCoords()) {
      let aHex = this.getHexStrCoord(hexCoords);
      if (aHex) {
        hexSet.add(aHex);
      }
    }

    if (null in hexSet) {
      throw new Error(`Null in hexSet! ${hexSet}`);
    } else {
      // console.log('HexSet: ', hexSet);
    }

    return hexSet;
  }

  getHexNeighborhoods(someHexes) {
    let allTheHexes = new Set();
  
    for (let targetHex of someHexes) {
      this.getHexAndAdjacent(targetHex).forEach(neighborHex => allTheHexes.add(neighborHex));
    }

    if (null in allTheHexes) {
      throw new Error(`Null in allTheHexes! ${allTheHexes}`);
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

  isOwnHexSelected() {
    if (!this.#selectedHex) {
      return false;
    }
    const selectedUnits = this.#selectedHex.getUnits();
    return selectedUnits && selectedUnits.length > 0 && selectedUnits[0].getOwningPlayer() === this.#players.getCurrentPlayer();
  }

  isOppositionHex(aHex) {
    if (aHex.getUnits().length == 0) {
      return false;
    }
    return aHex.getUnits()[0].getOwningPlayer() !== this.#players.getCurrentPlayer();
  }

  hasCombat() {
    for (let hex of this.getAllHexes()) {
      if (hex.hasCombat()) {
        return true;
      }
    }
    return false;
  }

  getOccupiedHexes() {
    const occupiedHexes = new Set();
    for (let unit of this.getUnits()) {
      occupiedHexes.add(unit.getContainingHex());
    }
    return occupiedHexes;
  }

  sparseBoard() {
    const sparseUnits = [];
    for (let unit of this.getUnits()) {
      let unitHex = unit.getContainingHex();
      sparseUnits.push({id: unit.getId(), row: unitHex.getRow(), column: unitHex.getColumn()})
    }
    return {
      units: sparseUnits
    };
  }
}
