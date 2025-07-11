import { eventBus } from '../event-bus.js';

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
      } else {
        const destinationHex = board.getHex(unit.row, unit.column);
        board.updateUnitPosition(boardUnit, containingHex, destinationHex);
      }
    }

    eventBus.emit('redraw');
    eventBus.emit('menuUpdate');
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