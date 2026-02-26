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
    line: jest.fn(),
    noStroke: jest.fn(),
    fill: jest.fn(),
    circle: jest.fn(),
  };
};

const createHexDrawer = ({ radius = 50 } = {}) => ({
  getHexRadius: jest.fn(() => radius),
  hexCenter: jest.fn(({ row, column }) => ({ x: column * 10, y: row * 10 })),
});

describe('RoadDrawer', () => {
  test('drawAll builds centerline segments and draws roads in two passes', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [
      new Road(roadType, [[9, 7], [9, 8], [8, 8], [7, 8], [6, 8], [5, 9], [4, 9], [4, 8], [3, 7]]),
      new Road(roadType, [[4, 9], [4, 10], [3, 11], [3, 12]]),
    ];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.drawAll();

    expect(p5.push).toHaveBeenCalledTimes(2);
    expect(p5.noFill).toHaveBeenCalledTimes(1);
    expect(p5.noStroke).toHaveBeenCalledTimes(1);
    expect(p5.strokeCap).toHaveBeenCalledWith(p5.ROUND);
    expect(p5.strokeJoin).toHaveBeenCalledWith(p5.ROUND);

    expect(p5.stroke).toHaveBeenNthCalledWith(1, 0x8A, 0x76, 0x50, 220);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(1, 50 * 0.33);
    expect(p5.stroke).toHaveBeenNthCalledWith(2, 0xC7, 0xB4, 0x8A, 205);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(2, 50 * 0.18);

    expect(p5.line).toHaveBeenCalled();
    const firstPassLines = p5.line.mock.calls.slice(0, p5.line.mock.calls.length / 2);
    const hasRawJunctionEndpoints = firstPassLines.some((args) => (
      (args[0] === 90 && args[1] === 40) || (args[2] === 90 && args[3] === 40)
    ));
    expect(hasRawJunctionEndpoints).toBe(false);

    expect(hexDrawer.hexCenter).toHaveBeenCalledWith({ row: 4, column: 9 });
    expect(p5.fill).toHaveBeenNthCalledWith(1, 0x8A, 0x76, 0x50, 220);
    expect(p5.fill).toHaveBeenNthCalledWith(2, 0xC7, 0xB4, 0x8A, 205);
    expect(p5.circle).toHaveBeenNthCalledWith(1, 90, 40, 50 * 0.24);
    expect(p5.circle).toHaveBeenNthCalledWith(2, 90, 40, 50 * 0.14);

    expect(p5.drawingContext.shadowBlur).toBe(0);
    expect(p5.drawingContext.shadowColor).toBe('rgba(0,0,0,0)');
    expect(p5.pop).toHaveBeenCalledTimes(2);
  });

  test('draw delegates to drawAll for compatibility', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.draw(new Hex(9, 9));

    expect(p5.line).toHaveBeenCalledTimes(2);
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
