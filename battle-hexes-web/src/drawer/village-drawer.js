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
    this.#p.stroke('#b2a897');
    this.#p.strokeWeight(1.5);

    const blockFills = ['#e4dfd2', '#ddd6c7', '#e2d9c6'];
    let fillIndex = 0;

    const blocks = [
      { x: center.x - radius * 0.32, y: center.y - radius * 0.18, w: blockSize * 1.05, h: blockSize * 0.9 },
      { x: center.x + radius * 0.14, y: center.y - radius * 0.22, w: blockSize * 0.95, h: blockSize * 1.05 },
      { x: center.x - radius * 0.28, y: center.y + radius * 0.16, w: blockSize * 0.9, h: blockSize * 1.1 },
      { x: center.x + radius * 0.18, y: center.y + radius * 0.06, w: blockSize * 1.15, h: blockSize * 0.8 },
      { x: center.x - radius * 0.02, y: center.y + radius * 0.3, w: blockSize * 1.25, h: blockSize * 0.95 },
    ];

    blocks.forEach(({ x, y, w, h }) => {
      this.#p.fill(blockFills[fillIndex % blockFills.length]);
      fillIndex += 1;
      this.#p.rect(x, y, w, h, 2);
    });
  }
}
