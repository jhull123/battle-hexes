import { Board } from "../src/board";
import { Faction } from "../src/faction";
import { Unit } from "../src/unit";

let board;
const redFaction = new Faction('Red Faction');
const blueFaction = new Faction('Blue Faction');
const redUnit = new Unit('Red Unit', redFaction);
const blueUnit = new Unit('Blue Unit', blueFaction);

beforeEach(() => {
  board = new Board(10, 10, [redFaction, blueFaction]);
});

describe('hasCombat', () => {
  test('hasCombat() is false when units are not adjacent', () => {
    board.addUnit(redUnit, 2, 3);
    board.addUnit(blueUnit, 8, 8);
    expect(board.getCombat().hasCombat()).toBe(false);
  });

  test('hasCombat() is true when opposing units are adjacent', () => {
    board.addUnit(redUnit, 2, 5);
    board.addUnit(blueUnit, 3, 4);
    expect(board.getCombat().hasCombat()).toBe(false);
  });
});

describe('getBattles', () => {
  test('getBattles() returns empty array when no battles', () => {
    board.addUnit(redUnit, 2, 3);
    board.addUnit(blueUnit, 8, 8);
    expect(board.getCombat().getBattles()).toEqual([]);
  });

  test('getBattles() returns one battle', () => {
    board.addUnit(redUnit, 2, 5);
    board.addUnit(blueUnit, 3, 4);
    expect(board.getCombat().getBattles().length).toBe(1);
  });

  test('getBattles() returns two battles', () => {
    board.addUnit(redUnit, 2, 5);
    board.addUnit(blueUnit, 3, 4);

    board.addUnit(new Unit('Red Unit', redFaction), 7, 8);
    board.addUnit(new Unit('Blue Unit', blueFaction), 8, 8);

    expect(board.getCombat().getBattles().length).toBe(2);
  });
});