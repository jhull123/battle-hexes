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

/*
const { Hex } = require('../battle'); // Assuming you are exporting Hex from battle.js

describe('Hex class', () => {
  test('should create a Hex with the given coordinates', () => {
    const hex = new Hex(3, 5);
    expect(hex.x).toBe(3);
    expect(hex.y).toBe(5);
  });
});
*/