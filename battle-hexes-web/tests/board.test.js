import { Board } from '../src/board.js';
import { Unit } from '../src/unit.js';

describe('addUnit', () => {
  let board, unit;

  beforeEach(() => {
    board = new Board();
    unit = new Unit();
  });

  test('adds unit to #units without row and column', () => {
    board.addUnit(unit);

    expect(board.getUnits().has(unit)).toBe(true); // Check unit added to units set
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