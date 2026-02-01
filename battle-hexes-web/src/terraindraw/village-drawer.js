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
      { dx: -0.55, dy: -0.5, w: 1.15, h: 0.78, angle: -0.28 }
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