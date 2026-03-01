import { TerrainHelper } from '../../src/terraindraw/terrain-helpers.js';

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
});

describe('TerrainHelper', () => {
  test('getHexVertices returns vertices from hexDrawer API when available', () => {
    const p5 = createMockP5();
    const expectedVertices = [
      { x: 1, y: 2 },
      { x: 3, y: 4 },
      { x: 5, y: 6 },
    ];
    const hexDrawer = {
      getHexVertices: jest.fn(() => expectedVertices),
    };

    const helper = new TerrainHelper(p5, hexDrawer);
    const vertices = helper.getHexVertices({ row: 1, column: 2 }, { x: 100, y: 100 }, 40);

    expect(vertices).toBe(expectedVertices);
    expect(hexDrawer.getHexVertices).toHaveBeenCalled();
  });

  test('samplePointInHex falls back to polar sampling when polygon sampling misses', () => {
    const p5 = createMockP5();
    p5.random = jest.fn((min, max) => {
      if (typeof min === 'undefined') {
        return 0.5;
      }

      if (typeof max === 'undefined') {
        return min;
      }

      return max;
    });
    const helper = new TerrainHelper(p5, {});
    const center = { x: 100, y: 200 };
    const placementRadius = 51;
    const tinyHex = [
      { x: 0, y: 0 },
      { x: 0.1, y: 0 },
      { x: 0.1, y: 0.1 },
      { x: 0, y: 0.1 },
    ];

    const point = helper.samplePointInHex(center, placementRadius, tinyHex);

    expect(point.x).toBeCloseTo(100 + (Math.sqrt(0.5) * placementRadius));
    expect(point.y).toBeCloseTo(200);
  });

  test('pickPosition retries candidates and accepts the first with enough spacing', () => {
    const p5 = createMockP5();
    const helper = new TerrainHelper(p5, {});
    const center = { x: 0, y: 0 };
    const hexVertices = [
      { x: -1, y: -1 },
      { x: 1, y: -1 },
      { x: 1, y: 1 },
      { x: -1, y: 1 },
    ];

    const candidateSequence = [{ x: 0, y: 0 }, { x: 5, y: 5 }];
    const sampleSpy = jest.spyOn(helper, 'samplePointInHex').mockImplementation(() => candidateSequence.shift());

    const point = helper.pickPosition(center, 10, hexVertices, [{ x: 0, y: 0 }], 2);

    expect(sampleSpy).toHaveBeenCalledTimes(2);
    expect(point).toEqual({ x: 5, y: 5 });
  });

  test('pickPosition returns fallback candidate when all attempts fail spacing', () => {
    const p5 = createMockP5();
    const helper = new TerrainHelper(p5, {});
    const center = { x: 10, y: 10 };
    const hexVertices = [
      { x: 0, y: 0 },
      { x: 1, y: 0 },
      { x: 1, y: 1 },
      { x: 0, y: 1 },
    ];

    const sampleSpy = jest.spyOn(helper, 'samplePointInHex').mockReturnValue({ x: 11, y: 11 });

    const point = helper.pickPosition(center, 10, hexVertices, [{ x: 11, y: 11 }], 2);

    expect(sampleSpy).toHaveBeenCalledTimes(15);
    expect(point).toEqual({ x: 11, y: 11 });
  });
});
