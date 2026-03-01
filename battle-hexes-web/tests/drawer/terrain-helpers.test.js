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
  test('getHexVertices uses hexDrawer.getHexVertices when available', () => {
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
    expect(hexDrawer.getHexVertices).toHaveBeenCalledWith({ row: 1, column: 2 }, 40);
  });

  test('getHexVertices fallback uses provided hex radius', () => {
    const p5 = createMockP5();
    const helper = new TerrainHelper(p5, {});
    const center = { x: 100, y: 100 };

    const vertices = helper.getHexVertices({ row: 0, column: 0 }, center, 40);

    expect(vertices).toHaveLength(6);
    vertices.forEach((vertex) => {
      const dx = vertex.x - center.x;
      const dy = vertex.y - center.y;
      expect(Math.sqrt(dx * dx + dy * dy)).toBeCloseTo(40);
    });
  });

  test('samplePointInHex returns center when polygon sampling misses', () => {
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
    const tinyHex = [
      { x: 0, y: 0 },
      { x: 0.1, y: 0 },
      { x: 0.1, y: 0.1 },
      { x: 0, y: 0.1 },
    ];

    const point = helper.samplePointInHex(center, tinyHex);

    expect(point).toEqual(center);
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

    const point = helper.pickPosition(center, hexVertices, [{ x: 0, y: 0 }], 2);

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

    const point = helper.pickPosition(center, hexVertices, [{ x: 11, y: 11 }], 2);

    expect(sampleSpy).toHaveBeenCalledTimes(15);
    expect(point).toEqual({ x: 11, y: 11 });
  });
});
