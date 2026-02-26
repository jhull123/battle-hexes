import {
  buildRoadGraph,
  getJunctionHexKeys,
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
    noStroke: jest.fn(),
    strokeCap: jest.fn(),
    strokeJoin: jest.fn(),
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    beginShape: jest.fn(),
    vertex: jest.fn(),
    endShape: jest.fn(),
    fill: jest.fn(),
    circle: jest.fn(),
  };
};

const createHexDrawer = ({ radius = 50 } = {}) => ({
  getHexRadius: jest.fn(() => radius),
  hexCenter: jest.fn(({ row, column }) => ({ x: column * 10, y: row * 10 })),
});

describe('buildRoadGraph', () => {
  test('straight road gives degree 2 in middle and degree 1 at endpoints', () => {
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4], [2, 5]])];

    const { degreesByHexKey } = buildRoadGraph(roads);

    expect(degreesByHexKey.get('2,3')).toBe(1);
    expect(degreesByHexKey.get('2,4')).toBe(2);
    expect(degreesByHexKey.get('2,5')).toBe(1);
  });

  test('crossroads marks shared hex with degree 3 and includes it in junction set', () => {
    const roads = [
      { path: [[4, 4], [4, 5], [4, 6]] },
      { path: [[3, 5], [4, 5]] },
    ];

    const { degreesByHexKey } = buildRoadGraph(roads);
    const junctionHexKeys = getJunctionHexKeys(roads);

    expect(degreesByHexKey.get('4,5')).toBe(3);
    expect(junctionHexKeys.has('4,5')).toBe(true);
  });

  test('deduplicates shared edges so degree is not inflated', () => {
    const roads = [
      { path: [[1, 1], [1, 2]] },
      { path: [[1, 2], [1, 1]] },
      { segments: [[1, 1], [2, 1]] },
    ];

    const { degreesByHexKey } = buildRoadGraph(roads);

    expect(degreesByHexKey.get('1,1')).toBe(2);
    expect(degreesByHexKey.get('1,2')).toBe(1);
    expect(degreesByHexKey.get('2,1')).toBe(1);
  });

  test('straight road has no junctions', () => {
    const roads = [{ path: [[0, 0], [0, 1], [0, 2]] }];

    const junctionHexKeys = getJunctionHexKeys(roads);

    expect(junctionHexKeys.size).toBe(0);
  });
});

describe('RoadDrawer', () => {
  test('drawAll renders roads as continuous polylines', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4], [3, 4]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.drawAll();

    expect(p5.push).toHaveBeenCalledTimes(1);
    expect(p5.noFill).toHaveBeenCalledTimes(1);
    expect(p5.strokeCap).toHaveBeenCalledWith(p5.ROUND);
    expect(p5.strokeJoin).toHaveBeenCalledWith(p5.ROUND);

    expect(p5.stroke).toHaveBeenNthCalledWith(1, 0x8A, 0x76, 0x50, 220);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(1, 50 * 0.33);
    expect(p5.stroke).toHaveBeenNthCalledWith(2, 0xC7, 0xB4, 0x8A, 205);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(2, 50 * 0.18);

    expect(p5.beginShape).toHaveBeenCalledTimes(2);
    expect(p5.vertex).toHaveBeenNthCalledWith(1, 30, 20);
    expect(p5.vertex).toHaveBeenNthCalledWith(2, 40, 20);
    expect(p5.vertex).toHaveBeenNthCalledWith(3, 40, 30);
    expect(p5.endShape).toHaveBeenCalledTimes(2);

    expect(p5.circle).not.toHaveBeenCalled();
    expect(p5.drawingContext.shadowBlur).toBe(0);
    expect(p5.drawingContext.shadowColor).toBe('rgba(0,0,0,0)');
    expect(p5.pop).toHaveBeenCalledTimes(1);
  });

  test('drawAll renders a small hub only for true junction hexes', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roads = [
      { path: [[4, 4], [4, 5], [4, 6]] },
      { path: [[3, 5], [4, 5]] },
    ];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.drawAll();

    expect(p5.circle).toHaveBeenCalledTimes(2);
    expect(p5.circle).toHaveBeenNthCalledWith(1, 50, 40, 50 * 0.22);
    expect(p5.circle).toHaveBeenNthCalledWith(2, 50, 40, 50 * 0.12);
  });

  test('draw delegates to drawAll for compatibility', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.draw(new Hex(9, 9));

    expect(p5.beginShape).toHaveBeenCalled();
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

    expect(p5.beginShape).not.toHaveBeenCalled();
    expect(p5.vertex).not.toHaveBeenCalled();
    expect(p5.endShape).not.toHaveBeenCalled();
    expect(p5.circle).not.toHaveBeenCalled();
  });
});
