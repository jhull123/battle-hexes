export class BoardUpdater {
  constructor() {
  }

  updateBoard(board, units) {
    for (const boardUnit of board.getUnits()) {
      const unit = this.#findUnit(boardUnit.getId(), units);
      const containingHex = boardUnit.getContainingHex();

      if (unit === null) {
        // unit was eliminated
        containingHex.removeUnit(boardUnit);
        continue;
      }

      const destinationHex = board.getHex(unit.row, unit.column);
      if (containingHex !== destinationHex) {
        // unit moved
        containingHex.removeUnit(boardUnit);
        destinationHex.addUnit(boardUnit);
        boardUnit.setContainingHex(destinationHex);
      }
    }
  }

  #findUnit(id, units) {
    for (const unit of units) {
      if (unit.id === id) {
        return unit;
      }
    }
    return null;
  }
}