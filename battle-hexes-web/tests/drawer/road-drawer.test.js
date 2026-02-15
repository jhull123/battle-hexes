import { RoadDrawer } from '../../src/drawer/road-drawer.js';
import { Hex } from '../../src/model/hex.js';
import { Road, RoadType } from '../../src/model/road.js';

const createMockP5 = () => ({
  stroke: jest.fn(),
  strokeWeight: jest.fn(),
  line: jest.fn(),
});

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

    expect(p5.stroke).toHaveBeenNthCalledWith(1, '#8A7650');
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(1, expect.any(Number));
    expect(p5.line).toHaveBeenNthCalledWith(1, 66.25, 200, 133.75, 200);

    expect(p5.stroke).toHaveBeenNthCalledWith(2, '#C7B48A');
    expect(p5.strokeWeight).toHaveBeenNthCalledWith(2, expect.any(Number));
    expect(p5.line).toHaveBeenNthCalledWith(2, 66.25, 200, 133.75, 200);
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
  });
});
