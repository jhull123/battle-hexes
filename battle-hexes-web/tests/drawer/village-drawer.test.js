import { VillageDrawer } from '../../src/drawer/village-drawer.js';

describe('VillageDrawer.draw', () => {
  const createP = () => ({
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    fill: jest.fn(),
    rectMode: jest.fn(),
    rect: jest.fn(),
    push: jest.fn(),
    pop: jest.fn(),
    translate: jest.fn(),
    rotate: jest.fn(),
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
    expect(p.push).toHaveBeenCalledTimes(21);
    expect(p.pop).toHaveBeenCalledTimes(21);
    expect(p.translate).toHaveBeenCalledTimes(21);
    expect(p.rotate).toHaveBeenCalledTimes(21);

    const angles = p.rotate.mock.calls.map(([angle]) => angle);
    const uniqueAngles = [...new Set(angles.map((value) => Math.round(value * 100)))];
    expect(uniqueAngles.length).toBeGreaterThanOrEqual(11);
    expect(angles.some((angle) => Math.abs(angle) > 0.15)).toBe(true);

    const calls = p.rect.mock.calls;
    const translations = p.translate.mock.calls;
    const sampled = translations.map((coords, index) => {
      const [x, y] = coords;
      const [, , w, h] = calls[index];
      return { x, y, w, h };
    });

    expect(sampled[0].x).toBeCloseTo(98.0, 1);
    expect(sampled[0].y).toBeCloseTo(140.0, 1);
    expect(sampled[0].w).toBeCloseTo(10.1, 1);
    expect(sampled[0].h).toBeCloseTo(6.9, 1);

    expect(sampled[11].x).toBeCloseTo(112.8, 1);
    expect(sampled[11].y).toBeCloseTo(162.4, 1);
    expect(sampled[11].w).toBeCloseTo(11.6, 1);
    expect(sampled[11].h).toBeCloseTo(7.7, 1);

    expect(sampled[20].x).toBeCloseTo(136.0, 1);
    expect(sampled[20].y).toBeCloseTo(184.0, 1);
    expect(sampled[20].w).toBeCloseTo(8.8, 1);
    expect(sampled[20].h).toBeCloseTo(7.2, 1);

    const minX = Math.min(...sampled.map(({ x, w }) => x - w / 2));
    const maxX = Math.max(...sampled.map(({ x, w }) => x + w / 2));
    const minY = Math.min(...sampled.map(({ y, h }) => y - h / 2));
    const maxY = Math.max(...sampled.map(({ y, h }) => y + h / 2));

    expect(maxX - minX).toBeGreaterThan(55);
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
