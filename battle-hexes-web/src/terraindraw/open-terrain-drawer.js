import { TerrainHelper } from './terrain-helpers.js';

export class OpenTerrainDrawer {
  #p;
  #hexDrawer;
  #terrainHelper;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
    this.#terrainHelper = new TerrainHelper(p, hexDrawer);
  }

  draw(aHex) {
    this.#p.randomSeed(aHex.hexSeed);

    const center = this.#hexDrawer.hexCenter(aHex);
    const radius = this.#hexDrawer.getHexRadius();
    const hexVertices = this.#terrainHelper.getHexVertices(aHex, center, radius);
    const tuftCount = Math.floor(this.#p.random(13)) + 12;
    const strokeWeight = Math.max(0.35, radius * 0.01);
    const alpha = Math.floor(this.#p.random(51, 78));
    const placedPoints = [];

    this.#p.stroke(0, alpha);
    this.#p.strokeWeight(strokeWeight);

    for (let i = 0; i < tuftCount; i += 1) {
      const minDist = this.#p.random(radius * 0.08, radius * 0.14);
      const { x, y } = this.#terrainHelper.pickPosition(center, hexVertices, placedPoints, minDist);
      const rotation = this.#p.random(-0.35, 0.35);
      const scale = this.#p.random(0.8, 1.2);
      const strokeCount = Math.floor(this.#p.random(3)) + 2;
      const bladeLength = this.#p.random(radius * 0.07, radius * 0.12);

      this.#drawTuftGlyph({
        x,
        y,
        rotation,
        scale,
        strokeCount,
        bladeLength,
      });
      placedPoints.push({ x, y });
    }

    this.#p.randomSeed();
  }

  #drawTuftGlyph({ x, y, rotation, scale, strokeCount, bladeLength }) {
    this.#p.push();
    this.#p.translate(x, y);
    this.#p.rotate(rotation);
    this.#p.scale(scale);

    for (let i = 0; i < strokeCount; i += 1) {
      const t = strokeCount === 1 ? 0.5 : i / (strokeCount - 1);
      const spread = (t - 0.5) * bladeLength * 0.8;
      const tipX = spread * 0.35;
      const tipY = -bladeLength * this.#p.random(0.65, 1);

      this.#p.line(0, 0, tipX + spread, tipY);
    }

    this.#p.pop();
  }

}
