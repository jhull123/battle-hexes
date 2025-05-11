import { Board } from '../../src/model/board.js';
import { BoardUpdater } from '../../src/model/board-updater.js';
import { Faction } from '../../src/model/faction.js';
import { Unit } from '../../src/model/unit.js';

describe('updateBoard', () => {
  let board, boardUpdater, factions, redUnit, blueUnit;

  beforeEach(() => {
    factions = [new Faction(), new Faction()];
    board = new Board(10, 10, factions);
    boardUpdater = new BoardUpdater();
    redUnit = new Unit('unit-001', 'Red Unit', factions[0]);
    blueUnit = new Unit('unit-002', 'Blue Unit', factions[1]);
  });

  test('update empty board with no units', () => {
    boardUpdater.updateBoard(board, []);
  });

  test('one unit no update', () => {
    board.addUnit(redUnit, 4, 5);
    boardUpdater.updateBoard(board, [{id: 'unit-001', row: 4, column: 5}]);
    expect(redUnit.getContainingHex().coordsHumanString()).toBe('4, 5');
  });

  test('one unit moves', () => {
    board.addUnit(redUnit, 4, 5);
    boardUpdater.updateBoard(board, [{id: 'unit-001', row: 6, column: 7}]);
    expect(redUnit.getContainingHex().coordsHumanString()).toBe('6, 7');
  });

  test('one unit eliminated', () => {
    board.addUnit(redUnit, 4, 5);
    boardUpdater.updateBoard(board, []);
    expect(redUnit.getContainingHex()).toBeNull();
    expect(board.getHex(4, 5).getUnits().length).toBe(0);
  });
});