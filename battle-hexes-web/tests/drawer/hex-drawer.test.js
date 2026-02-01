import { HexDrawer } from '../../src/drawer/hex-drawer.js';
import { Hex } from '../../src/model/hex.js';
import { Terrain } from '../../src/model/terrain.js';

class TestHexDrawer extends HexDrawer {
  constructor(...args) {
    super(...args);
    this.drawnHexes = [];
  }

  drawHex(hexToDraw, strokeColor, strokeSize, fillColor) {
    this.drawnHexes.push({
      hexToDraw,
      strokeColor,
      strokeSize,
      fillColor
    });
  }
}

const createMockP5 = () => ({
  TWO_PI: Math.PI * 2,
  cos: Math.cos,
  sin: Math.sin,
  stroke: jest.fn(),
  strokeWeight: jest.fn(),
  fill: jest.fn(),
  noFill: jest.fn(),
  beginShape: jest.fn(),
  vertex: jest.fn(),
  endShape: jest.fn(),
  CENTER: 'CENTER'
});

describe('HexDrawer.draw', () => {
  let p5;
  let hexDrawer;

  beforeEach(() => {
    p5 = createMockP5();
    hexDrawer = new TestHexDrawer(p5, 30);
  });

  test('uses terrain color when hex has terrain', () => {
    const terrain = new Terrain('forest', '#228B22');
    const hex = new Hex(5, 5);
    hex.setTerrain(terrain);

    hexDrawer.draw(hex);

    expect(hexDrawer.drawnHexes).toHaveLength(1);
    expect(hexDrawer.drawnHexes[0].fillColor).toBe('#228B22');
  });

  test('uses default color when hex has no terrain', () => {
    const hex = new Hex(5, 5);

    hexDrawer.draw(hex);

    expect(hexDrawer.drawnHexes).toHaveLength(1);
    expect(hexDrawer.drawnHexes[0].fillColor).toBe('#fffdd0');
  });
});
