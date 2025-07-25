import { MovementAnimator } from '../../src/animation/movement-animator.js';
jest.mock('../../src/animation/movement-animator.js', () => ({
  MovementAnimator: jest.fn().mockImplementation(() => ({
    animate: jest.fn(),
  })),
}));

import { Board } from '../../src/model/board.js';
import { Faction } from '../../src/model/faction.js';
import { Unit } from '../../src/model/unit.js';

describe('addUnit', () => {
  let factions, board, unit;

  beforeEach(() => {
    factions = [new Faction(), new Faction()];
    board = new Board(0, 0, factions);
    unit = new Unit();
  });

  test('adds unit to #units without row and column', () => {
    board.addUnit(unit);
    expect(board.getUnits().has(unit)).toBe(true); // Check unit added to units set
  });
});

describe('getAdjacentHexes', () => {
  let board;

  beforeEach(() => {
    board = new Board(10, 10, [new Faction(), new Faction()]);
  });

  test('getAdjacentHexesReturnsNeighboringHexes', () => {
    const aHex = board.getHex(5, 5);
    const adjacentHexes = board.getAdjacentHexes(aHex);
    expect(adjacentHexes.size).toBe(6);
    expect(adjacentHexes.has(board.getHex(4, 5))).toBe(true);
    expect(adjacentHexes.has(board.getHex(5, 4))).toBe(true);
    expect(adjacentHexes.has(board.getHex(6, 4))).toBe(true);
    expect(adjacentHexes.has(board.getHex(6, 5))).toBe(true);
    expect(adjacentHexes.has(board.getHex(6, 6))).toBe(true);
    expect(adjacentHexes.has(board.getHex(5, 6))).toBe(true);
  });
});

describe('getHexAndAdjacent', () => {
  let board;

  beforeEach(() => {
    board = new Board(10, 10, [new Faction(), new Faction()]);
  });

  test('getHexAndAdjacentReturnsHexAndNeighborings', () => {
    const aHex = board.getHex(5, 5);
    const adjacentHexes = board.getHexAndAdjacent(aHex);
    expect(adjacentHexes.size).toBe(7);
    expect(adjacentHexes.has(board.getHex(4, 5))).toBe(true);
    expect(adjacentHexes.has(board.getHex(5, 5))).toBe(true);
  });
});

describe('sparseBoard', () => {
  let board, redUnit, blueUnit;

  beforeEach(() => {
    redUnit = new Unit('unit-001');
    blueUnit = new Unit('unit-002');
    
    board = new Board(10, 10, []);
    board.addUnit(redUnit, 2, 3);
    board.addUnit(blueUnit, 2, 4);
  });

  test('sparse board returns data as json object', () => {
    const sparseBoard = board.sparseBoard();
    const sparseUnits = sparseBoard.units;

    expect(sparseUnits.length).toBe(2);

    const unitMap = new Map();
    for (let unit of sparseUnits) {
      unitMap[unit.id] = unit;
    }

    expect(unitMap['unit-001'].row).toBe(2);
    expect(unitMap['unit-001'].column).toBe(3);

    expect(unitMap['unit-002'].row).toBe(2);
    expect(unitMap['unit-002'].column).toBe(4)
  });
});

describe('animator integration', () => {
  test('getAnimator returns animator instance from constructor', () => {
    const board = new Board(1, 1);
    expect(typeof board.getAnimator().animate).toBe('function');
  });

  test('selectHex uses animator to animate movement', () => {
    const player = { isHuman: () => true };
    const factions = [new Faction('f1', 'f1', '#f00')];
    factions[0].setOwningPlayer(player);
    const board = new Board(1, 2);
    board.setPlayers({ getCurrentPlayer: () => player });
    const unit = new Unit('u1', 'Unit', factions[0], null, 1, 1, 1);
    board.addUnit(unit, 0, 0);

    const start = board.getHex(0, 0);
    const end = board.getHex(0, 1);

    const animatorInstance = board.getAnimator();
    board.selectHex(start);
    board.selectHex(end);

    expect(animatorInstance.animate).toHaveBeenCalledWith(unit, [start, end], true);
  });
});
