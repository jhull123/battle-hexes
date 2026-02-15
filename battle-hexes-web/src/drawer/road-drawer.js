export class RoadDrawer {
  #p;
  #hexDrawer;
  #getRoads;

  constructor(p, hexDrawer, getRoads) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
    this.#getRoads = getRoads;
  }

  draw(aHex) {
    if (!this.#hexHasRoad(aHex)) {
      return;
    }

    const center = this.#hexDrawer.hexCenter(aHex);
    const radius = this.#hexDrawer.getHexRadius();
    const roadLength = radius * 1.35;
    const x1 = center.x - roadLength / 2;
    const x2 = center.x + roadLength / 2;
    const y = center.y;
    const ctx = this.#p.drawingContext;

    this.#p.push();
    this.#p.strokeCap(this.#p.ROUND);
    this.#p.strokeJoin(this.#p.ROUND);

    ctx.shadowBlur = radius * 0.12;
    ctx.shadowColor = 'rgba(0,0,0,0.18)';
    this.#p.stroke(0x8A, 0x76, 0x50, 220);
    this.#p.strokeWeight(radius * 0.33);
    this.#p.line(x1, y, x2, y);

    ctx.shadowBlur = 0;
    ctx.shadowColor = 'rgba(0,0,0,0)';
    this.#p.stroke(0xC7, 0xB4, 0x8A, 205);
    this.#p.strokeWeight(radius * 0.18);
    this.#p.line(x1, y, x2, y);
    this.#p.pop();
  }

  #hexHasRoad(aHex) {
    for (const road of this.#getRoads()) {
      for (const [row, column] of road.path) {
        if (row === aHex.row && column === aHex.column) {
          return true;
        }
      }
    }

    return false;
  }
}
