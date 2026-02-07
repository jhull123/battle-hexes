import { HexDrawer } from '../../src/drawer/hex-drawer.js';
import { Hex } from '../../src/model/hex.js';
import { Terrain } from '../../src/model/terrain.js';

let mockResolve;
let mockTerrainDrawerResolverConstructor;

jest.mock('../../src/terraindraw/terrain-drawer-resolver.js', () => {
  mockTerrainDrawerResolverConstructor = jest.fn();
  mockResolve = jest.fn();
  mockTerrainDrawerResolverConstructor.mockImplementation(() => ({
    resolve: mockResolve
  }));
  return { TerrainDrawerResolver: mockTerrainDrawerResolverConstructor };
});

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
    mockResolve.mockReset();
    mockTerrainDrawerResolverConstructor.mockClear();
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

  test('draws terrain overlay when resolver returns a drawer', () => {
    const hex = new Hex(1, 2);
    const terrain = new Terrain('village', '#9b8f7a');
    hex.setTerrain(terrain);

    const terrainDrawer = { draw: jest.fn() };
    mockResolve.mockReturnValue(terrainDrawer);

    hexDrawer.draw(hex);

    expect(mockResolve).toHaveBeenCalledWith(hex);
    expect(terrainDrawer.draw).toHaveBeenCalledWith(hex);
  });

  test('skips terrain overlay when resolver returns null', () => {
    const hex = new Hex(3, 4);
    const terrain = new Terrain('village', '#9b8f7a');
    hex.setTerrain(terrain);

    mockResolve.mockReturnValue(null);

    hexDrawer.draw(hex);

    expect(mockResolve).toHaveBeenCalledWith(hex);
  });
});
