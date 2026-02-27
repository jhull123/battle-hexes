import { Hex } from '../../src/model/hex.js';
import { Objective } from '../../src/model/objective.js';
import { Terrain } from '../../src/model/terrain.js';
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

describe('terrain', () => {
  test('stores terrain reference', () => {
    const terrain = new Terrain('open', '#C6AA5C');

    hex.setTerrain(terrain);

    expect(hex.getTerrain()).toBe(terrain);
  });
});

describe('objectives', () => {
  test('stores objectives assigned to the hex', () => {
    const objective = new Objective('hold', 3);

    hex.addObjective(objective);

    expect(hex.getObjectives()).toEqual([objective]);
  });

  test('returns a copy of objectives', () => {
    const objective = new Objective('hold', 3);
    hex.addObjective(objective);

    const objectives = hex.getObjectives();
    objectives.push(new Objective('hold', 1));

    expect(hex.getObjectives()).toEqual([objective]);
  });
});

describe('hasMovableUnit', () => {
  test('returns false for empty hex', () => {
    expect(hex.hasMovableUnit()).toBe(false);
  });

  test('returns true when any unit is movable (not necessarily first)', () => {
    const unit1 = new Unit();
    const unit2 = new Unit();

    jest.spyOn(unit1, 'getMovesRemaining').mockReturnValue(0);
    jest.spyOn(unit1, 'getOwningPlayer').mockReturnValue({ isHuman: () => true });

    jest.spyOn(unit2, 'getMovesRemaining').mockReturnValue(1);
    jest.spyOn(unit2, 'getOwningPlayer').mockReturnValue({ isHuman: () => true });

    hex.addUnit(unit1);
    hex.addUnit(unit2);

    expect(hex.hasMovableUnit()).toBe(true);
  });

  test('returns false when no contained units are movable', () => {
    const unit1 = new Unit();
    const unit2 = new Unit();

    jest.spyOn(unit1, 'getMovesRemaining').mockReturnValue(0);
    jest.spyOn(unit1, 'getOwningPlayer').mockReturnValue({ isHuman: () => true });

    jest.spyOn(unit2, 'getMovesRemaining').mockReturnValue(0);
    jest.spyOn(unit2, 'getOwningPlayer').mockReturnValue({ isHuman: () => false });

    hex.addUnit(unit1);
    hex.addUnit(unit2);

    expect(hex.hasMovableUnit()).toBe(false);
  });
});
