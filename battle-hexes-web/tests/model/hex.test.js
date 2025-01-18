import { Hex } from '../../src/model/hex.js';
import { Unit } from '../../src/model/unit.js';

let hex;

beforeEach(() => {
  hex = new Hex(5, 5);
});

describe('hasCombat', () => {
  test('returns false for empty hex', () => {
    expect(hex.hasCombat()).toBe(false);
  });

  test('returns false when containing units do not have combat', () => {
    const mockUnit = new Unit();
    jest.spyOn(mockUnit, 'getCombatOpponents').mockReturnValue([]);
    hex.addUnit(mockUnit);

    expect(hex.hasCombat()).toBe(false);
  });


  test('returns true when containing units have combat', () => {
    const mockUnit = new Unit();
    jest.spyOn(mockUnit, 'getCombatOpponents').mockReturnValue([[new Unit()]]);
    hex.addUnit(mockUnit);

    expect(hex.hasCombat()).toBe(true);
  });
});