import { VillageDrawer } from '../../src/drawer/village-drawer.js';

describe('VillageDrawer.draw', () => {
  const createP = () => ({
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    fill: jest.fn(),
    rectMode: jest.fn(),
    rect: jest.fn(),
    line: jest.fn(),
    CENTER: 'center',
  });

  const createHexDrawer = () => ({
    drawHex: jest.fn(),
    hexCenter: jest.fn(() => ({ x: 120, y: 160 })),
    getHexRadius: jest.fn(() => 40),
  });

  const hex = { row: 1, column: 1 };

  test('draws a distinct village hex and clustered buildings', () => {
    const p = createP();
    const hexDrawer = createHexDrawer();
    const drawer = new VillageDrawer(p, hexDrawer);

    drawer.draw(hex);

    expect(hexDrawer.drawHex).toHaveBeenCalledWith(hex, '#2f3c2f', 2, '#d6e7c7');
    expect(p.rectMode).toHaveBeenCalledWith(p.CENTER);

    expect(p.stroke).toHaveBeenCalledWith('#b2a897');
    expect(p.strokeWeight).toHaveBeenCalledWith(1.5);

    expect(p.rect).toHaveBeenCalledTimes(5);
    expect(p.line).not.toHaveBeenCalled();
    expect(p.fill).toHaveBeenCalledTimes(5);

    const calls = p.rect.mock.calls;
    const [firstBuilding, secondBuilding, thirdBuilding, fourthBuilding, fifthBuilding] = calls;

    expect(firstBuilding[0]).toBeCloseTo(107.2, 1); // x
    expect(firstBuilding[1]).toBeCloseTo(152.8, 1); // y
    expect(firstBuilding[2]).toBeCloseTo(9.24, 2); // width
    expect(firstBuilding[3]).toBeCloseTo(7.92, 2); // height

    expect(secondBuilding[0]).toBeCloseTo(125.6, 1);
    expect(secondBuilding[1]).toBeCloseTo(151.2, 1);
    expect(secondBuilding[2]).toBeCloseTo(8.36, 2);
    expect(secondBuilding[3]).toBeCloseTo(9.24, 2);

    expect(thirdBuilding[0]).toBeCloseTo(108.8, 1);
    expect(thirdBuilding[1]).toBeCloseTo(166.4, 1);
    expect(thirdBuilding[2]).toBeCloseTo(7.92, 2);
    expect(thirdBuilding[3]).toBeCloseTo(9.68, 2);

    expect(fourthBuilding[0]).toBeCloseTo(127.2, 1);
    expect(fourthBuilding[1]).toBeCloseTo(162.4, 1);
    expect(fourthBuilding[2]).toBeCloseTo(10.12, 2);
    expect(fourthBuilding[3]).toBeCloseTo(7.04, 2);

    expect(fifthBuilding[0]).toBeCloseTo(119.2, 1);
    expect(fifthBuilding[1]).toBeCloseTo(172, 1);
    expect(fifthBuilding[2]).toBeCloseTo(11, 2);
    expect(fifthBuilding[3]).toBeCloseTo(8.36, 2);
  });
});
