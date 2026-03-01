const ROUGH_COLORS = ['#5E604E', '#70735C', '#8E9076'];
const OUTLINE_COLOR = '#3E3F33';

export class RoughDrawer {
  #p;
  #hexDrawer;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    this.#p.randomSeed(aHex.hexSeed);
    const center = this.#hexDrawer.hexCenter(aHex);
    const radius = this.#hexDrawer.getHexRadius();
    const innerRadius = radius * 0.82;
    const minDotSize = radius * 0.09;
    const maxDotSize = radius * 0.17;
    const dotCount = this.#p.random(10) + 14;

    this.#p.strokeWeight(Math.max(0.6, radius * 0.03));

    for (let i = 0; i < dotCount; i += 1) {
      const dotColor = ROUGH_COLORS[Math.floor(this.#p.random(ROUGH_COLORS.length))];
      const alpha = Math.floor(this.#p.random(120, 171));
      const angle = this.#p.random(this.#p.TWO_PI);
      const distance = Math.sqrt(this.#p.random()) * innerRadius;
      const x = center.x + this.#p.cos(angle) * distance;
      const y = center.y + this.#p.sin(angle) * distance;
      const diameter = this.#p.random(minDotSize, maxDotSize);

      this.#p.fill(dotColor + this.#toHexAlpha(alpha));
      this.#p.stroke(OUTLINE_COLOR + this.#toHexAlpha(alpha));
      // draw an oval with a flat bottom instead of a perfect circle
      const w = diameter;
      const h = diameter * 0.7; // height less than width gives a flattened look
      this.#p.beginShape();
      this.#p.vertex(x - w/2, y); // bottom left
      // left side curve up to top
      this.#p.bezierVertex(
        x - w/2, y - h/2,
        x - w/4, y - h,
        x,        y - h
      );
      // right side curve down back to bottom
      this.#p.bezierVertex(
        x + w/4, y - h,
        x + w/2, y - h/2,
        x + w/2, y
      );
      this.#p.endShape(this.#p.CLOSE);
    }

    this.#p.randomSeed();
  }

  #toHexAlpha(alpha) {
    return alpha.toString(16).padStart(2, '0').toUpperCase();
  }
}
