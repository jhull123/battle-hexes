import { Hex } from './hex.js';
import { Combat } from './combat.js';

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
      // console.log(`We have a move hover hex! ${this.#hoverHex}`);
      this.#hoverHex.setMoveHoverFromHex(this.getSelectedHex());
    }

    if (oldHover) {
      oldHover.setMoveHoverFromHex(undefined);
    }

    return oldHover;
  }

  getHexAndAdjacent(aHex) {
    if (aHex === undefined) {
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

  isOwnHexSelected() {
    if (!this.#selectedHex) {
      return false;
    }
    const selectedUnits = this.#selectedHex.getUnits();
    return selectedUnits && selectedUnits.length > 0 && selectedUnits[0].getFaction() === this.#factionTurn;
  }

  isOwnHex(aHex) {
    if (aHex.getUnits().length == 0) {
      return false;
    }
    return aHex.getUnits[0].getFaction() === this.#factionTurn;
  }

  isOppositionHex(aHex) {
    if (aHex.getUnits().length == 0) {
      return false;
    }
    return aHex.getUnits()[0].getFaction() !== this.#factionTurn;
  }

  hasCombat() {
    return new Combat(this.getUnits()).hasCombat();
  }

  getCombat() {
    return new Combat(this.getUnits());
  }

  getOccupiedHexes() {
    const occupiedHexes = new Set();
    for (let unit of this.getUnits()) {
      occupiedHexes.add(unit.getContainingHex());
    }
    return occupiedHexes;
  }
}
