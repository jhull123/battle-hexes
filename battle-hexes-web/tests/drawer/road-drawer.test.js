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
    strokeCap: jest.fn(),
    strokeJoin: jest.fn(),
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    line: jest.fn(),
  };
};

const createHexDrawer = ({ radius = 50, center = { x: 100, y: 200 } } = {}) => ({
  getHexRadius: jest.fn(() => radius),
  hexCenter: jest.fn(() => center),
});

describe('RoadDrawer.draw', () => {
  test('draws a two-tone horizontal road when a road crosses the hex', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 3], [2, 4]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.draw(new Hex(2, 3));

    expect(p5.push).toHaveBeenCalledTimes(1);
    expect(p5.strokeCap).toHaveBeenCalledWith(p5.ROUND);
    expect(p5.strokeJoin).toHaveBeenCalledWith(p5.ROUND);

    expect(p5.stroke).toHaveBeenNthCalledWith(1, 0x8A, 0x76, 0x50, 220);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(1, expect.any(Number));
    expect(p5.line).toHaveBeenNthCalledWith(1, 66.25, 200, 133.75, 200);

    expect(p5.stroke).toHaveBeenNthCalledWith(2, 0xC7, 0xB4, 0x8A, 205);
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(2, expect.any(Number));
    expect(p5.line).toHaveBeenNthCalledWith(2, 66.25, 200, 133.75, 200);

    expect(p5.drawingContext.shadowBlur).toBe(0);
    expect(p5.drawingContext.shadowColor).toBe('rgba(0,0,0,0)');
    expect(p5.pop).toHaveBeenCalledTimes(1);
  });

  test('does not draw anything when no road crosses the hex', () => {
    const p5 = createMockP5();
    const hexDrawer = createHexDrawer();
    const roadType = new RoadType('secondary', 1);
    const roads = [new Road(roadType, [[2, 4], [2, 5]])];
    const roadDrawer = new RoadDrawer(p5, hexDrawer, () => roads);

    roadDrawer.draw(new Hex(2, 3));

    expect(p5.stroke).not.toHaveBeenCalled();
    expect(p5.strokeWeight).not.toHaveBeenCalled();
    expect(p5.line).not.toHaveBeenCalled();
    expect(p5.push).not.toHaveBeenCalled();
    expect(p5.pop).not.toHaveBeenCalled();
  });
});
