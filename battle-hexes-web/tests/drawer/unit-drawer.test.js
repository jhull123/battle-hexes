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

describe('UnitDrawer.drawCounter echelon symbols', () => {
  const createP5Mock = () => ({
    CENTER: 'CENTER',
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    fill: jest.fn(),
    rectMode: jest.fn(),
    rect: jest.fn(),
    line: jest.fn(),
    noStroke: jest.fn(),
    textSize: jest.fn(),
    textAlign: jest.fn(),
    text: jest.fn(),
  });

  const createUnit = (echelon) => ({
    getFaction: () => ({
      getCounterColor: () => '#808080',
    }),
    getAttack: () => 4,
    getDefense: () => 3,
    getMovement: () => 2,
    getEchelon: () => echelon,
  });

  test('draws echelon symbol for known echelons', () => {
    const p5 = createP5Mock();
    const unitDrawer = new UnitDrawer(p5, createHexDrawer());

    unitDrawer.drawCounter(createUnit('division'), 100, 100);

    expect(p5.text).toHaveBeenCalledWith('XX', 100, expect.any(Number));
  });

  test('omits echelon text when echelon is undefined', () => {
    const p5 = createP5Mock();
    const unitDrawer = new UnitDrawer(p5, createHexDrawer());

    unitDrawer.drawCounter(createUnit(undefined), 100, 100);

    expect(p5.text).toHaveBeenCalledTimes(1);
    expect(p5.text).toHaveBeenCalledWith('4-3-2', 100, expect.any(Number));
  });
});

describe('UnitDrawer.drawCounter defensive fire icon', () => {
  const createP5Mock = () => ({
    CENTER: 'CENTER',
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    fill: jest.fn(),
    rectMode: jest.fn(),
    rect: jest.fn(),
    line: jest.fn(),
    noStroke: jest.fn(),
    textSize: jest.fn(),
    textAlign: jest.fn(),
    text: jest.fn(),
  });

  const createUnit = () => ({
    getFaction: () => ({
      getCounterColor: () => '#808080',
    }),
    getAttack: () => 4,
    getDefense: () => 3,
    getMovement: () => 2,
    getEchelon: () => 'division',
  });

  test('draws a borderless inset icon with specified ammo-mark colors and line proportions', () => {
    const p5 = createP5Mock();
    const unitDrawer = new UnitDrawer(p5, createHexDrawer());

    unitDrawer.drawCounter(createUnit(), 100, 100);

    const counterSide = 30 * 1.3;
    const iconSide = counterSide * 0.18;
    const iconPadding = counterSide * 0.08;
    const iconX = 100 + counterSide / 2 - iconPadding - iconSide / 2;
    const iconY = 100 - counterSide / 2 + iconPadding + iconSide / 2;

    expect(p5.rect).toHaveBeenCalledWith(iconX, iconY, iconSide, iconSide);

    expect(p5.noStroke).toHaveBeenCalled();
    expect(p5.fill).toHaveBeenCalledWith('#2B2B2B');
    expect(p5.fill).toHaveBeenCalledWith('#FAF9F6');
  });
});

