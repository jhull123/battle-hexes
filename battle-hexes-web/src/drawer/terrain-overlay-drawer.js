import { TerrainDrawerResolver } from '../terraindraw/terrain-drawer-resolver.js';

export class TerrainOverlayDrawer {
  #terrainDrawerResolver;

  constructor(p, hexDrawer) {
    this.#terrainDrawerResolver = new TerrainDrawerResolver(p, hexDrawer);
  }

  draw(aHex) {
    this.#terrainDrawerResolver.resolve(aHex)?.draw(aHex);
  }
}
