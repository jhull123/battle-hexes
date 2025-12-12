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

    expect(p.stroke).toHaveBeenCalledWith('#7f705b');
    expect(p.strokeWeight).toHaveBeenCalledWith(1.25);

    expect(p.rect).toHaveBeenCalledTimes(21);
    expect(p.line).not.toHaveBeenCalled();
    expect(p.fill).toHaveBeenCalledTimes(21);

    const calls = p.rect.mock.calls;
    const sampled = calls.map(([x, y, w, h]) => ({ x, y, w, h }));

    expect(sampled[0].x).toBeCloseTo(97.6, 1);
    expect(sampled[0].y).toBeCloseTo(139.2, 1);
    expect(sampled[0].w).toBeCloseTo(9.2, 1);
    expect(sampled[0].h).toBeCloseTo(9.0, 1);

    expect(sampled[10].x).toBeCloseTo(112, 1);
    expect(sampled[10].y).toBeCloseTo(160, 1);
    expect(sampled[10].w).toBeCloseTo(9.8, 1);
    expect(sampled[10].h).toBeCloseTo(8.4, 1);

    expect(sampled[20].x).toBeCloseTo(140.8, 1);
    expect(sampled[20].y).toBeCloseTo(180.8, 1);
    expect(sampled[20].w).toBeCloseTo(10.9, 1);
    expect(sampled[20].h).toBeCloseTo(10, 1);

    const minX = Math.min(...calls.map(([x, , w]) => x - w / 2));
    const maxX = Math.max(...calls.map(([x, , w]) => x + w / 2));
    const minY = Math.min(...calls.map(([ , y, , h]) => y - h / 2));
    const maxY = Math.max(...calls.map(([ , y, , h]) => y + h / 2));

    expect(maxX - minX).toBeGreaterThan(60);
    expect(maxY - minY).toBeGreaterThan(50);

    const overlaps = [];
    for (let i = 0; i < sampled.length; i += 1) {
      for (let j = i + 1; j < sampled.length; j += 1) {
        const a = sampled[i];
        const b = sampled[j];
        const dx = Math.abs(a.x - b.x);
        const dy = Math.abs(a.y - b.y);
        if (dx < (a.w + b.w) / 2 && dy < (a.h + b.h) / 2) {
          overlaps.push([i, j]);
        }
      }
    }

    expect(overlaps).toHaveLength(0);
  });
});
