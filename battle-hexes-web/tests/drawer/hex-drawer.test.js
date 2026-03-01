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
      fillColor,
    });
  }
}

const createMockP5 = () => ({
  TWO_PI: Math.PI * 2,
  CLOSE: 'CLOSE',
  cos: Math.cos,
  sin: Math.sin,
  stroke: jest.fn(),
  strokeWeight: jest.fn(),
  fill: jest.fn(),
  noFill: jest.fn(),
  beginShape: jest.fn(),
  vertex: jest.fn(),
  endShape: jest.fn(),
  CENTER: 'CENTER',
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

describe('HexDrawer geometry', () => {
  test('getHexVertices returns six vertices on the requested radius', () => {
    const p5 = createMockP5();
    const hexDrawer = new HexDrawer(p5, 30);
    const hex = new Hex(0, 0);

    const center = hexDrawer.hexCenter(hex);
    const vertices = hexDrawer.getHexVertices(hex);

    expect(vertices).toHaveLength(6);
    vertices.forEach((vertex) => {
      const dx = vertex.x - center.x;
      const dy = vertex.y - center.y;
      expect(Math.sqrt(dx * dx + dy * dy)).toBeCloseTo(30);
    });
  });

  test('drawHex uses getHexVertices output as the rendered polygon', () => {
    const p5 = createMockP5();
    const hexDrawer = new HexDrawer(p5, 30);
    const hex = new Hex(0, 0);
    const expectedVertices = hexDrawer.getHexVertices(hex);

    hexDrawer.drawHex(hex, '#202020', 2, '#fffdd0');

    expect(p5.vertex).toHaveBeenCalledTimes(6);
    expectedVertices.forEach((vertex, index) => {
      expect(p5.vertex).toHaveBeenNthCalledWith(index + 1, vertex.x, vertex.y);
    });
  });
});
