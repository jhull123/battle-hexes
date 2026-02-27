import { TerrainOverlayDrawer } from '../../src/drawer/terrain-overlay-drawer.js';

let mockResolve;
let mockTerrainDrawerResolverConstructor;

jest.mock('../../src/terraindraw/terrain-drawer-resolver.js', () => {
  mockTerrainDrawerResolverConstructor = jest.fn();
  mockResolve = jest.fn();
  mockTerrainDrawerResolverConstructor.mockImplementation(() => ({
    resolve: mockResolve,
  }));
  return { TerrainDrawerResolver: mockTerrainDrawerResolverConstructor };
});

describe('TerrainOverlayDrawer.draw', () => {
  beforeEach(() => {
    mockResolve.mockReset();
    mockTerrainDrawerResolverConstructor.mockClear();
  });

  test('draws terrain overlay when resolver returns a drawer', () => {
    const terrainOverlayDrawer = new TerrainOverlayDrawer({}, {});
    const hex = { id: 'hex-1' };
    const terrainDrawer = { draw: jest.fn() };
    mockResolve.mockReturnValue(terrainDrawer);

    terrainOverlayDrawer.draw(hex);

    expect(mockResolve).toHaveBeenCalledWith(hex);
    expect(terrainDrawer.draw).toHaveBeenCalledWith(hex);
  });

  test('skips terrain overlay when resolver returns null', () => {
    const terrainOverlayDrawer = new TerrainOverlayDrawer({}, {});
    const hex = { id: 'hex-1' };
    mockResolve.mockReturnValue(null);

    terrainOverlayDrawer.draw(hex);

    expect(mockResolve).toHaveBeenCalledWith(hex);
  });
});
