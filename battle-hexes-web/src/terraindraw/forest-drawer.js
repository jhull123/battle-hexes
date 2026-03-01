const PINE_FILL_COLORS = ['#4F5B44', '#606C52'];
const PINE_OUTLINE_COLOR = '#2F3528';

export class ForestDrawer {
  #p;
  #hexDrawer;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    const row = aHex.getRow?.() ?? aHex.row ?? 0;
    const column = aHex.getColumn?.() ?? aHex.column ?? 0;
    this.#p.randomSeed(this.#seedFromCoords(row, column));

    const center = this.#hexDrawer.hexCenter(aHex);
    const radius = this.#hexDrawer.getHexRadius();
    const innerRadius = radius * 0.68;
    const treeCount = Math.max(8, Math.floor(radius * 0.16 + this.#p.random(11) + 8));
    const strokeWeight = Math.max(0.4, radius * 0.016);

    this.#p.stroke(PINE_OUTLINE_COLOR);
    this.#p.strokeWeight(strokeWeight);

    for (let i = 0; i < treeCount; i += 1) {
      const angle = this.#p.random(this.#p.TWO_PI);
      const distance = Math.sqrt(this.#p.random()) * innerRadius;
      const x = center.x + this.#p.cos(angle) * distance;
      const y = center.y + this.#p.sin(angle) * distance;
      const treeHeight = this.#p.random(radius * 0.15, radius * 0.24);
      const treeWidth = treeHeight * this.#p.random(0.55, 0.72);
      const rotation = this.#p.random(-0.1745, 0.1745);
      const fillColor = PINE_FILL_COLORS[Math.floor(this.#p.random(PINE_FILL_COLORS.length))];
      const layerCount = this.#p.random() < 0.5 ? 1 : 2;

      this.#drawPineGlyph(x, y, treeWidth, treeHeight, rotation, fillColor, layerCount);
    }

    this.#p.randomSeed();
  }

  #drawPineGlyph(x, y, width, height, rotation, fillColor, layerCount) {
    this.#p.push();
    this.#p.translate(x, y);
    this.#p.rotate(rotation);
    this.#p.fill(fillColor);

    if (layerCount === 2) {
      this.#p.triangle(-width * 0.42, -height * 0.3, width * 0.42, -height * 0.3, 0, -height);
      this.#p.triangle(-width * 0.5, height * 0.06, width * 0.5, height * 0.06, 0, -height * 0.55);
    } else {
      this.#p.triangle(-width * 0.52, height * 0.05, width * 0.52, height * 0.05, 0, -height);
    }

    this.#p.line(0, height * 0.04, 0, height * 0.28);
    this.#p.pop();
  }

  #seedFromCoords(row, column) {
    const rowPart = (row * 73856093) >>> 0;
    const colPart = (column * 19349663) >>> 0;
    return (rowPart ^ colPart) >>> 0;
  }
}
