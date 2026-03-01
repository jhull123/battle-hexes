import { RoughDrawer } from "./rough-drawer.js";
import { VillageDrawer } from "./village-drawer.js";
import { ForestDrawer } from "./forest-drawer.js";

export class TerrainDrawerResolver {
  #terrainMap;

  constructor(p, hexDrawer) {
    this.#terrainMap = new Map([
      ["village", new VillageDrawer(p, hexDrawer)],
      ["rough", new RoughDrawer(p, hexDrawer)],
      ["forest", new ForestDrawer(p, hexDrawer)]
    ]);
  }

  resolve(aHex) {
    const terrainName = aHex.getTerrain()?.name;
    return this.#terrainMap.get(terrainName) ?? null;
  }
}
