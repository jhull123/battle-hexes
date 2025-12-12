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

    expect(p.rect).toHaveBeenCalledTimes(3);
    expect(p.line).toHaveBeenCalledTimes(6);

    const calls = p.rect.mock.calls;
    const [firstBuilding, secondBuilding, thirdBuilding] = calls;

    expect(firstBuilding[0]).toBeCloseTo(108.8, 1); // x
    expect(firstBuilding[1]).toBeCloseTo(160.96, 2); // y
    expect(firstBuilding[2]).toBeCloseTo(14, 1); // width
    expect(firstBuilding[3]).toBeCloseTo(8.8, 1); // height

    expect(secondBuilding[0]).toBeCloseTo(131.2, 1);
    expect(secondBuilding[1]).toBeCloseTo(160.48, 2);
    expect(secondBuilding[2]).toBeCloseTo(13.3, 1);
    expect(secondBuilding[3]).toBeCloseTo(8.8, 1);

    expect(thirdBuilding[0]).toBeCloseTo(120);
    expect(thirdBuilding[1]).toBeCloseTo(152.96, 2);
    expect(thirdBuilding[2]).toBeCloseTo(15.4, 1);
    expect(thirdBuilding[3]).toBeCloseTo(8.8, 1);
  });
});
