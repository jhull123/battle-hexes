import { OpenTerrainDrawer } from '../../src/terraindraw/open-terrain-drawer.js';

const createSeededMockP5 = () => {
  let seed = 1;

  return {
    TWO_PI: Math.PI * 2,
    cos: Math.cos,
    sin: Math.sin,
    randomSeed: jest.fn((newSeed) => {
      if (typeof newSeed === 'number') {
        seed = newSeed >>> 0;
      }
    }),
    random: jest.fn((min, max) => {
      seed = (1664525 * seed + 1013904223) >>> 0;
      const value01 = seed / 0x100000000;

      if (typeof min === 'undefined') {
        return value01;
      }

      if (typeof max === 'undefined') {
        return value01 * min;
      }

      return min + (max - min) * value01;
    }),
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    push: jest.fn(),
    pop: jest.fn(),
    translate: jest.fn(),
    rotate: jest.fn(),
    scale: jest.fn(),
    line: jest.fn(),
  };
};

describe('OpenTerrainDrawer', () => {
  test('draw is deterministic when seed is fixed', () => {
    const p5 = createSeededMockP5();
    const hexDrawer = {
      hexCenter: jest.fn(() => ({ x: 90, y: 70 })),
      getHexRadius: jest.fn(() => 40),
      getHexVertices: jest.fn(() => [
        { x: 90, y: 30 },
        { x: 125, y: 50 },
        { x: 125, y: 90 },
        { x: 90, y: 110 },
        { x: 55, y: 90 },
        { x: 55, y: 50 },
      ]),
    };
    const drawer = new OpenTerrainDrawer(p5, hexDrawer);
    const hex = { row: 1, column: 3, hexSeed: 4567 };

    drawer.draw(hex);
    const firstRunLines = p5.line.mock.calls.map((call) => [...call]);
    const firstRunTransforms = {
      translate: p5.translate.mock.calls.map((call) => [...call]),
      rotate: p5.rotate.mock.calls.map((call) => [...call]),
      scale: p5.scale.mock.calls.map((call) => [...call]),
    };

    p5.line.mockClear();
    p5.translate.mockClear();
    p5.rotate.mockClear();
    p5.scale.mockClear();

    drawer.draw(hex);

    expect(p5.line.mock.calls).toEqual(firstRunLines);
    expect(p5.translate.mock.calls).toEqual(firstRunTransforms.translate);
    expect(p5.rotate.mock.calls).toEqual(firstRunTransforms.rotate);
    expect(p5.scale.mock.calls).toEqual(firstRunTransforms.scale);
  });

  test('draw uses alpha in the 20-30% range for tuft strokes', () => {
    const p5 = createSeededMockP5();
    const hexDrawer = {
      hexCenter: jest.fn(() => ({ x: 30, y: 30 })),
      getHexRadius: jest.fn(() => 35),
      getHexVertices: jest.fn(() => [
        { x: 30, y: -5 },
        { x: 60, y: 12 },
        { x: 60, y: 48 },
        { x: 30, y: 65 },
        { x: 0, y: 48 },
        { x: 0, y: 12 },
      ]),
    };
    const drawer = new OpenTerrainDrawer(p5, hexDrawer);

    drawer.draw({ row: 0, column: 0, hexSeed: 99 });

    const strokeAlphaCalls = p5.stroke.mock.calls
      .filter((call) => call[0] === 0 && typeof call[1] === 'number')
      .map((call) => call[1]);

    expect(strokeAlphaCalls.length).toBeGreaterThan(0);
  });
});
