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

    expect(p.rect).toHaveBeenCalledTimes(7);
    expect(p.line).not.toHaveBeenCalled();
    expect(p.fill).toHaveBeenCalledTimes(7);

    const calls = p.rect.mock.calls;
    const [firstBuilding, secondBuilding, thirdBuilding, fourthBuilding, fifthBuilding, sixthBuilding, seventhBuilding] = calls;

    expect(firstBuilding[0]).toBeCloseTo(98, 1); // x
    expect(firstBuilding[1]).toBeCloseTo(152.8, 1); // y
    expect(firstBuilding[2]).toBeCloseTo(16.2, 1); // width
    expect(firstBuilding[3]).toBeCloseTo(11.4, 1); // height

    expect(secondBuilding[0]).toBeCloseTo(113.6, 1);
    expect(secondBuilding[1]).toBeCloseTo(143.2, 1);
    expect(secondBuilding[2]).toBeCloseTo(13.8, 1);
    expect(secondBuilding[3]).toBeCloseTo(10.2, 1);

    expect(thirdBuilding[0]).toBeCloseTo(135.2, 1);
    expect(thirdBuilding[1]).toBeCloseTo(148.8, 1);
    expect(thirdBuilding[2]).toBeCloseTo(16.2, 1);
    expect(thirdBuilding[3]).toBeCloseTo(13.2, 1);

    expect(fourthBuilding[0]).toBeCloseTo(105.6, 1);
    expect(fourthBuilding[1]).toBeCloseTo(163.2, 1);
    expect(fourthBuilding[2]).toBeCloseTo(12.6, 1);
    expect(fourthBuilding[3]).toBeCloseTo(16.2, 1);

    expect(fifthBuilding[0]).toBeCloseTo(123.2, 1);
    expect(fifthBuilding[1]).toBeCloseTo(160.8, 1);
    expect(fifthBuilding[2]).toBeCloseTo(18.6, 1);
    expect(fifthBuilding[3]).toBeCloseTo(12.6, 1);

    expect(sixthBuilding[0]).toBeCloseTo(137.6, 1);
    expect(sixthBuilding[1]).toBeCloseTo(168.8, 1);
    expect(sixthBuilding[2]).toBeCloseTo(13.8, 1);
    expect(sixthBuilding[3]).toBeCloseTo(15.6, 1);

    expect(seventhBuilding[0]).toBeCloseTo(119.2, 1);
    expect(seventhBuilding[1]).toBeCloseTo(180, 1);
    expect(seventhBuilding[2]).toBeCloseTo(16.8, 1);
    expect(seventhBuilding[3]).toBeCloseTo(11.4, 1);

    const minX = Math.min(...calls.map(([x, , w]) => x - w / 2));
    const maxX = Math.max(...calls.map(([x, , w]) => x + w / 2));
    const minY = Math.min(...calls.map(([ , y, , h]) => y - h / 2));
    const maxY = Math.max(...calls.map(([ , y, , h]) => y + h / 2));

    expect(maxX - minX).toBeGreaterThan(50);
    expect(maxY - minY).toBeGreaterThan(45);
  });
});
