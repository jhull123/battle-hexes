export class VillageDrawer {
  #p;
  #hexDrawer;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    const center = this.#hexDrawer.hexCenter(aHex);
    const radius = this.#hexDrawer.getHexRadius();
    const blockSize = radius * 0.22;

    this.#p.rectMode(this.#p.CENTER);
    this.#p.stroke('#7f705b');
    this.#p.strokeWeight(1.25);

    const blockFills = ['#c9ba9e', '#c3b79f', '#cdbfa4'];
    let fillIndex = 0;

    const blocks = [
      // outbuildings
      { dx: -0.42, dy: -0.72, w: 1.15, h: 0.78, angle: -0.20 },
      { dx: -0.19, dy: -0.75, w: 0.55, h: 0.62, angle: -0.21 },

      { dx: 0.51, dy: 0.68, w: 0.81, h: 0.75, angle: -0.03 },
      { dx: 0.27, dy: 0.66, w: 0.75, h: 0.76, angle:  0.01 },

      // first row
      { dx: -0.39, dy: -0.19, w: 1.20, h: 0.79, angle:  0.04 },
      { dx: -0.40, dy:  0.19, w: 1.22, h: 0.82, angle: -0.07 },

      { dx: -0.05, dy: -0.16, w: 1.20, h: 0.79, angle: -0.02 },
      { dx: -0.06, dy:  0.16, w: 1.22, h: 0.82, angle:  0.02 },
      
      { dx: 0.24, dy: -0.16, w: 1.20, h: 0.79, angle: -0.06 },
      { dx: 0.26, dy:  0.16, w: 1.22, h: 0.82, angle:  0.02 },
      
      // second row top
      { dx: -0.23, dy: -0.45, w: 1.06, h: 0.74, angle: 0.04 },
      { dx:  0.16, dy: -0.40, w: 1.30, h: 0.74, angle: -0.04 },

      // second row bottom
      { dx: -0.16, dy:  0.44, w: 1.36, h: 0.78, angle: -0.08 },

      // church
      { dx: 0.59, dy:  0.01, w: 1.25, h: 1.84, angle:  0.02 }
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