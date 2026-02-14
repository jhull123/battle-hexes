import { Road, RoadType } from '../../src/model/road';

describe('Road', () => {
  test('exposes type name, movement cost and path coordinates', () => {
    const type = new RoadType('secondary', 1.0);
    const road = new Road(type, [[5, 0], [5, 1], [6, 2]]);

    expect(road.type).toBe('secondary');
    expect(road.movementCost).toBe(1.0);
    expect(road.path).toEqual([[5, 0], [5, 1], [6, 2]]);
  });
});
