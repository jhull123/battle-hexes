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
    const blockSize = radius * 0.3;

    this.#p.rectMode(this.#p.CENTER);
    this.#p.stroke('#b2a897');
    this.#p.strokeWeight(1.5);

    const blockFills = ['#e5dfcf', '#ded7c6', '#e2dccd', '#d8d2c4'];
    let fillIndex = 0;

    const blocks = [
      { x: center.x - radius * 0.55, y: center.y - radius * 0.18, w: blockSize * 1.35, h: blockSize * 0.95 },
      { x: center.x - radius * 0.16, y: center.y - radius * 0.42, w: blockSize * 1.15, h: blockSize * 0.85 },
      { x: center.x + radius * 0.38, y: center.y - radius * 0.28, w: blockSize * 1.35, h: blockSize * 1.1 },
      { x: center.x - radius * 0.36, y: center.y + radius * 0.08, w: blockSize * 1.05, h: blockSize * 1.35 },
      { x: center.x + radius * 0.08, y: center.y + radius * 0.02, w: blockSize * 1.55, h: blockSize * 1.05 },
      { x: center.x + radius * 0.44, y: center.y + radius * 0.22, w: blockSize * 1.15, h: blockSize * 1.3 },
      { x: center.x - radius * 0.02, y: center.y + radius * 0.5, w: blockSize * 1.4, h: blockSize * 0.95 },
    ];

    blocks.forEach(({ x, y, w, h }) => {
      this.#p.fill(blockFills[fillIndex % blockFills.length]);
      fillIndex += 1;
      this.#p.rect(x, y, w, h, 2);
    });
  }
}
