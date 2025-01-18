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
