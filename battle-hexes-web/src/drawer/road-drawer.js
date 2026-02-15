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

    this.#p.stroke('#8A7650');
    this.#p.strokeWeight(radius * 0.33);
    this.#p.line(center.x - roadLength / 2, center.y, center.x + roadLength / 2, center.y);

    this.#p.stroke('#C7B48A');
    this.#p.strokeWeight(radius * 0.18);
    this.#p.line(center.x - roadLength / 2, center.y, center.x + roadLength / 2, center.y);
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
