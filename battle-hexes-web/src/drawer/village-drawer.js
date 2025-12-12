export class VillageDrawer {
  #p;
  #hexDrawer;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    const strokeColor = '#2f3c2f';
    const fillColor = '#d6e7c7';

    this.#hexDrawer.drawHex(aHex, strokeColor, 2, fillColor);

    const center = this.#hexDrawer.hexCenter(aHex);
    const radius = this.#hexDrawer.getHexRadius();
    const blockSize = radius * 0.23;

    this.#p.rectMode(this.#p.CENTER);
    this.#p.stroke('#7f705b');
    this.#p.strokeWeight(1.25);

    const blockFills = ['#c9ba9e', '#c3b79f', '#cdbfa4'];
    let fillIndex = 0;

    const blocks = [
      { dx: -0.56, dy: -0.52, w: 1.0, h: 0.9789 },
      { dx: -0.26, dy: -0.52, w: 1.0667, h: 0.9752 },
      { dx: 0.04, dy: -0.52, w: 1.1496, h: 1.0314 },
      { dx: 0.34, dy: -0.52, w: 1.0353, h: 0.9073 },
      { dx: -0.6, dy: -0.26, w: 1.0095, h: 1.0608 },
      { dx: -0.32, dy: -0.26, w: 1.0376, h: 1.0116 },
      { dx: -0.02, dy: -0.26, w: 1.1232, h: 0.9207 },
      { dx: 0.28, dy: -0.26, w: 1.0401, h: 1.0178 },
      { dx: 0.56, dy: -0.26, w: 1.0034, h: 0.9046 },
      { dx: -0.5, dy: 0, w: 1.0376, h: 0.9401 },
      { dx: -0.2, dy: 0, w: 1.0631, h: 0.9121 },
      { dx: 0.1, dy: 0, w: 1.1917, h: 1.0583 },
      { dx: 0.4, dy: 0, w: 1.1346, h: 1.0162 },
      { dx: 0.72, dy: 0, w: 1.069, h: 1.0924 },
      { dx: -0.36, dy: 0.26, w: 1.062, h: 0.9207 },
      { dx: -0.08, dy: 0.26, w: 1.1827, h: 0.9573 },
      { dx: 0.22, dy: 0.26, w: 1.1968, h: 0.9285 },
      { dx: 0.5, dy: 0.26, w: 1.0521, h: 1.0969 },
      { dx: -0.06, dy: 0.52, w: 1.2245, h: 0.9538 },
      { dx: 0.24, dy: 0.52, w: 1.2433, h: 0.9192 },
      { dx: 0.52, dy: 0.52, w: 1.1853, h: 1.0895 },
    ];

    blocks.forEach(({ dx, dy, w, h }) => {
      this.#p.fill(blockFills[fillIndex % blockFills.length]);
      fillIndex += 1;
      const x = center.x + radius * dx;
      const y = center.y + radius * dy;
      this.#p.rect(x, y, blockSize * w, blockSize * h, 2.2);
    });
  }
}
