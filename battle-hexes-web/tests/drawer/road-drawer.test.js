import {
  getRoadConnectionsForHex,
  RoadDrawer,
} from '../../src/drawer/road-drawer.js';
import { Hex } from '../../src/model/hex.js';
import { Road, RoadType } from '../../src/model/road.js';

const createMockP5 = () => {
  const drawingContext = {
    shadowBlur: 0,
    shadowColor: '',
  };

  return {
    ROUND: 'round',
    drawingContext,
    push: jest.fn(),
    pop: jest.fn(),
    noFill: jest.fn(),
    strokeCap: jest.fn(),
    strokeJoin: jest.fn(),
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    line: jest.fn(),
    circle: jest.fn(),
  };
};

const createHexDrawer = ({ radius = 50 } = {}) => ({
  getHexRadius: jest.fn(() => radius),
  hexCenter: jest.fn(({ row, column }) => ({ x: column * 10, y: row * 10 })),
});

describe('getRoadConnectionsForHex', () => {
  test('returns two neighbors for a normal through segment', () => {
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4], [3, 4]])];

    const neighbors = getRoadConnectionsForHex(roads, { row: 2, column: 4 });

    expect(neighbors).toEqual(
      expect.arrayContaining([
        { row: 2, column: 3 },
        { row: 3, column: 4 },
      ])
    );
    expect(neighbors).toHaveLength(2);
  });

  test('returns one neighbor for a road endpoint', () => {
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4], [3, 4]])];

    const neighbors = getRoadConnectionsForHex(roads, { row: 2, column: 3 });

    expect(neighbors).toEqual([{ row: 2, column: 4 }]);
  });

  test('returns three neighbors for crossroads in d_day_crossroads scenario layout', () => {
    const roads = [
      { path: [[4, 4], [4, 5], [4, 6]] },
      { path: [[3, 5], [4, 5]] },
    ];

    const neighbors = getRoadConnectionsForHex(roads, { row: 4, column: 5 });

    expect(neighbors).toEqual(
      expect.arrayContaining([
        { row: 4, column: 4 },
        { row: 4, column: 6 },
        { row: 3, column: 5 },
      ])
    );
    expect(neighbors).toHaveLength(3);
  });

  test('deduplicates neighbors that come from multiple roads and supports segments property', () => {
    const roads = [
      { path: [[1, 1], [1, 2]] },
      { path: [[1, 2], [1, 1]] },
      { segments: [[1, 1], [2, 1]] },
    ];

    const neighbors = getRoadConnectionsForHex(roads, { row: 1, column: 1 });

    expect(neighbors).toEqual(
      expect.arrayContaining([
        { row: 1, column: 2 },
        { row: 2, column: 1 },
      ])
    );
    expect(neighbors).toHaveLength(2);
  });
});

describe('RoadDrawer', () => {
  test('drawAll renders spokes and hub for each road hex with road connections', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4], [3, 4]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.drawAll();

    expect(p5.push).toHaveBeenCalledTimes(3);
    expect(p5.strokeCap).toHaveBeenCalledWith(p5.ROUND);
    expect(p5.strokeJoin).toHaveBeenCalledWith(p5.ROUND);

    expect(p5.stroke).toHaveBeenNthCalledWith(1, 0x8A, 0x76, 0x50, 220);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(1, 50 * 0.33);
    expect(p5.stroke).toHaveBeenNthCalledWith(2, 0xC7, 0xB4, 0x8A, 205);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(2, 50 * 0.18);

    expect(p5.line).toHaveBeenCalled();
    expect(p5.circle).toHaveBeenCalled();

    expect(p5.drawingContext.shadowBlur).toBe(0);
    expect(p5.drawingContext.shadowColor).toBe('rgba(0,0,0,0)');
    expect(p5.pop).toHaveBeenCalledTimes(3);
  });

  test('draw delegates to drawAll for compatibility', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.draw(new Hex(9, 9));

    expect(p5.line).toHaveBeenCalled();
    expect(hexDrawer.hexCenter).toHaveBeenCalledWith({ row: 2, column: 3 });
    expect(hexDrawer.hexCenter).toHaveBeenCalledWith({ row: 2, column: 4 });
  });

  test('drawAll skips roads with fewer than two points', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.drawAll();

    expect(p5.push).not.toHaveBeenCalled();
    expect(p5.line).not.toHaveBeenCalled();
    expect(p5.circle).not.toHaveBeenCalled();
  });
});
