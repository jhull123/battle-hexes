import { eventBus } from '../event-bus.js';

export class BoardUpdater {
  constructor() {
  }

  clearMoveHoverIllegalReasons(board) {
    for (const hex of board.getAllHexes()) {
      hex.setMoveHoverIllegalReason(undefined);
    }
  }

  updateBoard(board, units = [], { defensiveFireEvents = [] } = {}) {
    const unitsById = new Map((units ?? []).map((unit) => [unit.id, unit]));

    for (const boardUnit of board.getUnits()) {
      const unit = unitsById.get(boardUnit.getId()) ?? null;
      const containingHex = boardUnit.getContainingHex();

      if (unit === null) {
        board.getAnimator?.().interrupt?.(boardUnit);
        board.removeUnit(boardUnit);
      } else {
        const destinationHex = board.getHex(unit.row, unit.column);
        if (containingHex !== destinationHex) {
          board.getAnimator?.().interrupt?.(boardUnit);
        }
        board.updateUnitPosition(boardUnit, containingHex, destinationHex);
        if (Object.hasOwn(unit, 'defensive_fire_available')) {
          boardUnit.setDefensiveFireAvailable(unit.defensive_fire_available);
        }
      }
    }

    board.refreshCombat();

    if (Array.isArray(defensiveFireEvents) && defensiveFireEvents.length > 0) {
      eventBus.emit('defensiveFireResolved', defensiveFireEvents);
    }

    eventBus.emit('redraw');
    eventBus.emit('menuUpdate');
  }
}
