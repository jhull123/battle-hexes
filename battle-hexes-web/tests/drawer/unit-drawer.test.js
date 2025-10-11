import { UnitDrawer } from '../../src/drawer/unit-drawer.js';

class TestUnitDrawer extends UnitDrawer {
  constructor(...args) {
    super(...args);
    this.drawnCounters = [];
  }

  drawCounter(unit, x, y) {
    this.drawnCounters.push({ unit, x, y });
  }
}

const createHexDrawer = ({ radius = 30, center = { x: 100, y: 100 } } = {}) => ({
  getHexRadius: jest.fn(() => radius),
  hexCenter: jest.fn(() => center),
});

const createHex = (units = []) => ({
  getUnits: jest.fn(() => units),
});

describe('UnitDrawer.draw', () => {
  let hexDrawer;
  let unitDrawer;

  beforeEach(() => {
    hexDrawer = createHexDrawer();
    unitDrawer = new TestUnitDrawer({}, hexDrawer);
  });

  test('does not draw counters for empty hexes', () => {
    const hex = createHex([]);

    unitDrawer.draw(hex);

    expect(hexDrawer.hexCenter).not.toHaveBeenCalled();
    expect(unitDrawer.drawnCounters).toHaveLength(0);
  });

  test('draws a single unit at the hex center', () => {
    const unit = { id: 'unit-1' };
    const hex = createHex([unit]);

    unitDrawer.draw(hex);

    expect(unitDrawer.drawnCounters).toEqual([
      { unit, x: 100, y: 100 },
    ]);
  });

  test('stacks additional units up and to the right', () => {
    const units = [{ id: 'unit-1' }, { id: 'unit-2' }, { id: 'unit-3' }];
    const hex = createHex(units);

    unitDrawer.draw(hex);

    const expectedOffset = 30 * 1.3 * 0.2;

    expect(unitDrawer.drawnCounters).toHaveLength(3);
    expect(unitDrawer.drawnCounters[0]).toMatchObject({ unit: units[0], x: 100, y: 100 });
    expect(unitDrawer.drawnCounters[1].unit).toBe(units[1]);
    expect(unitDrawer.drawnCounters[1].x).toBeCloseTo(100 + expectedOffset);
    expect(unitDrawer.drawnCounters[1].y).toBeCloseTo(100 - expectedOffset);
    expect(unitDrawer.drawnCounters[2].unit).toBe(units[2]);
    expect(unitDrawer.drawnCounters[2].x).toBeCloseTo(100 + expectedOffset * 2);
    expect(unitDrawer.drawnCounters[2].y).toBeCloseTo(100 - expectedOffset * 2);
  });
});
