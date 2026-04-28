import { Board } from '../../src/model/board.js';
import { BoardUpdater } from '../../src/model/board-updater.js';
import { eventBus } from '../../src/event-bus.js';
import { Faction } from '../../src/model/faction.js';
import { Unit } from '../../src/model/unit.js';

jest.mock('../../src/event-bus.js', () => ({
  eventBus: {
    emit: jest.fn(),
    on: jest.fn(),
  },
}));

describe('updateBoard', () => {
  let board, boardUpdater, factions, redUnit, blueUnit;

  beforeEach(() => {
    eventBus.emit.mockClear();
    factions = [new Faction(), new Faction()];
    board = new Board(10, 10, factions);
    boardUpdater = new BoardUpdater();
    redUnit = new Unit('unit-001', 'Red Unit', factions[0]);
    blueUnit = new Unit('unit-002', 'Blue Unit', factions[1]);
  });

  test('update empty board with no units', () => {
    boardUpdater.updateBoard(board, []);
    expect(eventBus.emit).toHaveBeenCalledTimes(2);
    expect(eventBus.emit).toHaveBeenCalledWith('redraw');
    expect(eventBus.emit).toHaveBeenCalledWith('menuUpdate');
  });

  test('one unit no update', () => {
    board.addUnit(redUnit, 4, 5);
    boardUpdater.updateBoard(board, [{id: 'unit-001', row: 4, column: 5}]);
    expect(redUnit.getContainingHex().coordsHumanString()).toBe('4, 5');
    expect(eventBus.emit).toHaveBeenCalledTimes(2);
    expect(eventBus.emit).toHaveBeenCalledWith('redraw');
    expect(eventBus.emit).toHaveBeenCalledWith('menuUpdate');
  });

  test('one unit moves', () => {
    board.addUnit(redUnit, 4, 5);
    boardUpdater.updateBoard(board, [{id: 'unit-001', row: 6, column: 7}]);
    expect(redUnit.getContainingHex().coordsHumanString()).toBe('6, 7');
    expect(eventBus.emit).toHaveBeenCalledTimes(2);
    expect(eventBus.emit).toHaveBeenCalledWith('redraw');
    expect(eventBus.emit).toHaveBeenCalledWith('menuUpdate');
  });


  test('syncs defensive fire availability from server payload', () => {
    board.addUnit(redUnit, 4, 5);
    redUnit.setDefensiveFireAvailable(true);

    boardUpdater.updateBoard(board, [{
      id: 'unit-001',
      row: 4,
      column: 5,
      defensive_fire_available: false,
    }]);

    expect(redUnit.hasDefensiveFire()).toBe(false);
  });

  test('emits defensive fire events from authoritative movement results', () => {
    board.addUnit(redUnit, 4, 5);

    const defensiveFireEvents = [{
      firing_unit_id: 'unit-002',
      target_unit_id: 'unit-001',
      outcome: 'retreat',
      message: 'Defensive fire forced the target to retreat to (3, 5).',
    }];

    boardUpdater.updateBoard(board, [{ id: 'unit-001', row: 3, column: 5 }], { defensiveFireEvents });

    expect(redUnit.getContainingHex().coordsHumanString()).toBe('3, 5');
    expect(eventBus.emit).toHaveBeenCalledWith('defensiveFireResolved', defensiveFireEvents);
  });

  test('one unit eliminated', () => {
    board.addUnit(redUnit, 4, 5);
    boardUpdater.updateBoard(board, []);
    expect(redUnit.getContainingHex()).toBeNull();
    expect(board.getHex(4, 5).getUnits().length).toBe(0);
    expect(board.getUnits().has(redUnit)).toBe(false);
    expect(eventBus.emit).toHaveBeenCalledTimes(2);
    expect(eventBus.emit).toHaveBeenCalledWith('redraw');
    expect(eventBus.emit).toHaveBeenCalledWith('menuUpdate');
  });

  test('units adjacent after update trigger combat', () => {
    const player1 = { isHuman: () => true };
    const player2 = { isHuman: () => false };
    factions[0].setOwningPlayer(player1);
    factions[1].setOwningPlayer(player2);
    board.players = { getCurrentPlayer: () => player1 };

    board.addUnit(redUnit, 2, 2);
    board.addUnit(blueUnit, 4, 4);

    boardUpdater.updateBoard(board, [
      { id: 'unit-001', row: 3, column: 3 },
      { id: 'unit-002', row: 3, column: 4 }
    ]);

    expect(board.hasCombat()).toBe(true);
  });
});
