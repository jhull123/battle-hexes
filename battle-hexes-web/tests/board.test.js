import { Board } from '../src/board.js';
import { Faction } from '../src/faction.js';
import { Unit } from '../src/unit.js';

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

describe('endTurn', () => {
  let factions, board;

  beforeEach(() => {
    factions = [new Faction('Faction One'), new Faction('Faction Two')];
    board = new Board(0, 0, factions);
  });

  test('end turn switches turn to second faction when its the first factions turn', () => {
    const currentFaction = board.endTurn();
    expect(currentFaction).toBe(factions[1]);
  });

  test('end turn switches turn to first faction when its the last factions turn', () => {
    board.endTurn();
    const currentFaction = board.endTurn();
    expect(currentFaction).toBe(factions[0]);
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
