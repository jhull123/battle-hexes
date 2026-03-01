import { ForestDrawer } from '../../src/terraindraw/forest-drawer.js';

const createMockP5 = () => ({
  TWO_PI: Math.PI * 2,
  cos: Math.cos,
  sin: Math.sin,
  random: jest.fn((min, max) => {
    if (typeof min === 'undefined') {
      return 0.5;
    }

    if (typeof max === 'undefined') {
      return min * 0.5;
    }

    return min + (max - min) * 0.5;
  }),
  randomSeed: jest.fn(),
  stroke: jest.fn(),
  strokeWeight: jest.fn(),
  fill: jest.fn(),
  push: jest.fn(),
  pop: jest.fn(),
  translate: jest.fn(),
  rotate: jest.fn(),
  triangle: jest.fn(),
  line: jest.fn(),
});

describe('ForestDrawer', () => {
  test('draw renders deterministic pine glyphs inside the hex', () => {
    const p5 = createMockP5();
    const hexDrawer = {
      hexCenter: jest.fn(() => ({ x: 100, y: 100 })),
      getHexRadius: jest.fn(() => 40),
    };
    const forestDrawer = new ForestDrawer(p5, hexDrawer);
    const hex = {
      getRow: jest.fn(() => 3),
      getColumn: jest.fn(() => 5),
    };

    forestDrawer.draw(hex);

    expect(p5.randomSeed).toHaveBeenCalledTimes(2);
    expect(p5.randomSeed.mock.calls[0][0]).toBe(149986828);
    expect(p5.randomSeed.mock.calls[1][0]).toBeUndefined();
    expect(p5.stroke).toHaveBeenCalledWith('#2F3528');
    expect(p5.strokeWeight).toHaveBeenCalledWith(0.64);

    expect(p5.fill).toHaveBeenCalled();
    const fills = p5.fill.mock.calls.map((call) => call[0]);
    expect(fills.every((color) => color === '#4F5B44' || color === '#606C52')).toBe(true);

    expect(p5.push).toHaveBeenCalledTimes(19);
    expect(p5.pop).toHaveBeenCalledTimes(19);
    expect(p5.triangle).toHaveBeenCalledTimes(38);
    expect(p5.line).toHaveBeenCalledTimes(19);

    expect(p5.rotate).toHaveBeenCalledWith(0);
  });

  test('draw supports direct row/column properties and applies minimum stroke weight', () => {
    const p5 = createMockP5();
    const hexDrawer = {
      hexCenter: jest.fn(() => ({ x: 0, y: 0 })),
      getHexRadius: jest.fn(() => 5),
    };
    const forestDrawer = new ForestDrawer(p5, hexDrawer);

    forestDrawer.draw({ row: 1, column: 2 });

    expect(p5.push).toHaveBeenCalledTimes(14);
    expect(p5.line).toHaveBeenCalledTimes(14);
    expect(p5.strokeWeight).toHaveBeenCalledWith(0.4);
  });
});
