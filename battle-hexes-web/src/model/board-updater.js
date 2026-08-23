import { eventBus } from '../event-bus.js';
import { Unit } from './unit.js';

export class BoardUpdater {
  constructor() {
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
        unitsById.delete(boardUnit.getId());
        const destinationHex = board.getHex(unit.row, unit.column);
        if (containingHex !== destinationHex) {
          board.getAnimator?.().interrupt?.(boardUnit);
        }
        board.updateUnitPosition(boardUnit, containingHex, destinationHex);
        if (Object.hasOwn(unit, 'defensiveFireAvailable')) {
          boardUnit.setDefensiveFireAvailable(unit.defensiveFireAvailable);
        }
      }
    }

    for (const unitData of unitsById.values()) {
      const unit = this.#createUnit(board, unitData);
      if (unit !== null) {
        board.addUnit(unit, unitData.row, unitData.column);
      }
    }

    board.refreshCombat();

    if (Array.isArray(defensiveFireEvents) && defensiveFireEvents.length > 0) {
      eventBus.emit('defensiveFireResolved', defensiveFireEvents);
    }

    eventBus.emit('redraw');
    eventBus.emit('menuUpdate');
  }

  #createUnit(board, unitData) {
    if (!Object.hasOwn(unitData, 'factionId')) {
      return null;
    }
    const faction = board.getPlayers().getAllPlayers()
      .flatMap((player) => player.getFactions())
      .find((candidate) => candidate.getId() === unitData.factionId);
    if (!faction) {
      return null;
    }
    return new Unit(
      unitData.id,
      unitData.name,
      faction,
      unitData.type,
      unitData.attack,
      unitData.defense,
      unitData.move,
      unitData.echelon,
      unitData.defensiveFireAvailable ?? true,
    );
  }
}
