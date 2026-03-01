import {
  getBoardPixelHeight,
  getBoardPixelWidth,
  getCanvasDimensions,
} from '../../src/drawer/canvas-dimensions.js';

describe('canvas dimensions', () => {
  test('getBoardPixelWidth calculates full board width from columns and radius', () => {
    const width = getBoardPixelWidth(18, 50);

    expect(width).toBe(1375);
  });

  test('getBoardPixelHeight calculates board height including odd-column offset and top vertex', () => {
    const height = getBoardPixelHeight(11, 18, 50);

    expect(height).toBeCloseTo(1002.6279, 3);
  });

  test('getCanvasDimensions ensures width is at least the board width', () => {
    const dimensions = getCanvasDimensions({
      rows: 11,
      columns: 18,
      hexRadius: 50,
      windowWidth: 1200,
      menuWidth: 300,
      canvasMargin: 20,
    });

    expect(dimensions.width).toBe(1375);
    expect(dimensions.height).toBe(1003);
  });

  test('getCanvasDimensions expands width to available space when board is narrower', () => {
    const dimensions = getCanvasDimensions({
      rows: 5,
      columns: 4,
      hexRadius: 30,
      windowWidth: 1400,
      menuWidth: 300,
      canvasMargin: 20,
    });

    expect(dimensions.width).toBe(1080);
  });
});
