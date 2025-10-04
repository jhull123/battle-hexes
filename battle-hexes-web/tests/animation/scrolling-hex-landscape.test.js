import { ScrollingHexLandscape, DEFAULT_SCROLL_SPEED } from '../../src/animation/scrolling-hex-landscape.js';

describe('ScrollingHexLandscape', () => {
  let p;
  let hexDrawer;

  beforeEach(() => {
    p = {
      push: jest.fn(),
      pop: jest.fn(),
      translate: jest.fn(),
    };

    hexDrawer = {
      drawHex: jest.fn(),
      setShowHexCoords: jest.fn(),
    };
  });

  test('initial resize calculates a grid that covers the viewport', () => {
    const landscape = new ScrollingHexLandscape(p, { hexRadius: 50, hexDrawer });
    landscape.resize(800, 600);

    const gridSize = landscape.getVisibleGridSize();

    expect(gridSize.columns).toBeGreaterThan(0);
    expect(gridSize.rows).toBeGreaterThan(0);
    expect(hexDrawer.setShowHexCoords).toHaveBeenCalledWith(false);
  });

  test('draw renders the grid using the supplied drawer', () => {
    const landscape = new ScrollingHexLandscape(p, { hexRadius: 40, hexDrawer });
    landscape.resize(200, 160);

    landscape.draw(16);

    expect(p.push).toHaveBeenCalled();
    expect(p.pop).toHaveBeenCalled();
    expect(hexDrawer.drawHex).toHaveBeenCalled();
  });

  test('scroll speed can be tuned for animation pacing', () => {
    const landscape = new ScrollingHexLandscape(p, { hexRadius: 40, hexDrawer });
    landscape.resize(200, 160);

    landscape.draw(1000);
    const firstTranslateCall = p.translate.mock.calls.at(-1);

    landscape.setScrollSpeed(0);
    landscape.draw(1000);
    const secondTranslateCall = p.translate.mock.calls.at(-1);

    expect(firstTranslateCall[0]).not.toBeCloseTo(0);
    expect(secondTranslateCall[0]).toBeCloseTo(firstTranslateCall[0]);
    expect(landscape.getScrollSpeed()).toBe(0);
    expect(DEFAULT_SCROLL_SPEED).toBeGreaterThan(0);
  });
});
