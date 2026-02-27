import { RoadDrawer } from '../../src/drawer/road-drawer.js';
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
    beginShape: jest.fn(),
    curveVertex: jest.fn(),
    endShape: jest.fn(),
  };
};

const createHexDrawer = ({ radius = 50 } = {}) => ({
  getHexRadius: jest.fn(() => radius),
  hexCenter: jest.fn(({ row, column }) => ({ x: column * 10, y: row * 10 })),
});

describe('RoadDrawer', () => {
  test('drawAll renders smooth two-pass curves and avoids junction dot overlays', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [
      new Road(roadType, [[9, 7], [9, 8], [8, 8], [7, 8], [6, 8], [5, 9], [4, 9], [4, 8], [3, 7]]),
      new Road(roadType, [[4, 9], [4, 10], [3, 11], [3, 12]]),
    ];
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

    expect(p5.beginShape).toHaveBeenCalled();
    expect(p5.curveVertex).toHaveBeenCalled();
    expect(p5.endShape).toHaveBeenCalled();

    const includesJunctionCenter = p5.curveVertex.mock.calls.some(
      ([x, y]) => x === 90 && y === 40
    );
    expect(includesJunctionCenter).toBe(false);

    expect(hexDrawer.hexCenter).toHaveBeenCalledWith({ row: 4, column: 9 });

    expect(p5.drawingContext.shadowBlur).toBe(0);
    expect(p5.drawingContext.shadowColor).toBe('rgba(0,0,0,0)');
    expect(p5.pop).toHaveBeenCalledTimes(1);
  });

  test('draw delegates to drawAll for compatibility', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.draw(new Hex(9, 9));

    expect(p5.beginShape).toHaveBeenCalledTimes(2);
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
    expect(p5.beginShape).not.toHaveBeenCalled();
    expect(p5.curveVertex).not.toHaveBeenCalled();
    expect(p5.endShape).not.toHaveBeenCalled();
  });
});
