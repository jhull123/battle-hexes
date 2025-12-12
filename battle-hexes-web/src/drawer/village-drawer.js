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
    const blockSize = radius * 0.22;

    this.#p.rectMode(this.#p.CENTER);
    this.#p.stroke('#7f705b');
    this.#p.strokeWeight(1.25);

    const blockFills = ['#c9ba9e', '#c3b79f', '#cdbfa4'];
    let fillIndex = 0;

    const blocks = [
      { dx: -0.55, dy: -0.5, w: 1.15, h: 0.78, angle: -0.28 },
      { dx: -0.25, dy: -0.55, w: 1.35, h: 0.82, angle: -0.07 },
      { dx: 0.05, dy: -0.52, w: 1.05, h: 0.96, angle: 0.18 },
      { dx: 0.37, dy: -0.46, w: 1.28, h: 0.74, angle: 0.09 },
      { dx: 0.65, dy: -0.42, w: 1.12, h: 0.86, angle: -0.22 },

      { dx: -0.62, dy: -0.22, w: 1.05, h: 1.04, angle: 0.12 },
      { dx: -0.32, dy: -0.2, w: 1.28, h: 0.92, angle: -0.18 },
      { dx: 0.0, dy: -0.2, w: 1.14, h: 0.82, angle: 0.14 },
      { dx: 0.32, dy: -0.22, w: 1.16, h: 1.02, angle: -0.12 },
      { dx: 0.64, dy: -0.18, w: 1.08, h: 0.9, angle: 0.21 },

      { dx: -0.5, dy: 0.08, w: 1.22, h: 0.9, angle: -0.09 },
      { dx: -0.18, dy: 0.06, w: 1.32, h: 0.88, angle: 0.24 },
      { dx: 0.14, dy: 0.04, w: 1.18, h: 0.98, angle: -0.16 },
      { dx: 0.44, dy: 0.06, w: 1.1, h: 0.94, angle: 0.08 },
      { dx: 0.74, dy: 0.06, w: 1.04, h: 0.92, angle: -0.2 },

      { dx: -0.36, dy: 0.38, w: 1.26, h: 0.92, angle: 0.18 },
      { dx: -0.04, dy: 0.36, w: 1.18, h: 0.88, angle: -0.11 },
      { dx: 0.28, dy: 0.36, w: 1.16, h: 0.86, angle: 0.17 },
      { dx: 0.58, dy: 0.34, w: 1.08, h: 0.92, angle: -0.2 },

      { dx: 0.12, dy: 0.64, w: 1.2, h: 0.9, angle: 0.1 },
      { dx: 0.4, dy: 0.6, w: 1.0, h: 0.82, angle: -0.12 },
    ];

    blocks.forEach(({ dx, dy, w, h, angle }) => {
      this.#p.fill(blockFills[fillIndex % blockFills.length]);
      fillIndex += 1;
      const x = center.x + radius * dx;
      const y = center.y + radius * dy;
      this.#p.push();
      this.#p.translate(x, y);
      this.#p.rotate(angle);
      this.#p.rect(0, 0, blockSize * w, blockSize * h, 2.2);
      this.#p.pop();
    });
  }
}
