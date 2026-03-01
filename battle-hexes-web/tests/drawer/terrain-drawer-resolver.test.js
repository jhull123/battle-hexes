import { TerrainDrawerResolver } from '../../src/terraindraw/terrain-drawer-resolver.js';

describe('TerrainDrawerResolver', () => {
  test('resolves rough terrain to a drawer instance', () => {
    const resolver = new TerrainDrawerResolver({}, {});
    const hex = {
      getTerrain: jest.fn(() => ({ name: 'rough' })),
    };

    const drawer = resolver.resolve(hex);

    expect(drawer).not.toBeNull();
    expect(typeof drawer.draw).toBe('function');
  });

  test('resolves village terrain to a drawer instance', () => {
    const resolver = new TerrainDrawerResolver({}, {});
    const hex = {
      getTerrain: jest.fn(() => ({ name: 'village' })),
    };

    const drawer = resolver.resolve(hex);

    expect(drawer).not.toBeNull();
    expect(typeof drawer.draw).toBe('function');
  });

  test('returns null when no terrain drawer is registered', () => {
    const resolver = new TerrainDrawerResolver({}, {});
    const hex = {
      getTerrain: jest.fn(() => ({ name: 'forest' })),
    };

    expect(resolver.resolve(hex)).toBeNull();
  });
});
