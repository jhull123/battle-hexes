export class RoadDrawer {
  #p;
  #hexDrawer;
  #getRoads;

  constructor(p, hexDrawer, getRoads) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
    this.#getRoads = getRoads;
  }

  draw() {
    this.drawAll();
  }

  drawAll() {
    const radius = this.#hexDrawer.getHexRadius();

    for (const road of this.#getRoads()) {
      const points = road.path.map(([row, column]) =>
        this.#hexDrawer.hexCenter({ row, column })
      );

      this.#drawRoadCurve(points, radius);
    }
  }

  #drawRoadCurve(points, radius) {
    if (points.length < 2) {
      return;
    }

    const first = points[0];
    const last = points[points.length - 1];
    const ctx = this.#p.drawingContext;

    this.#p.push();
    this.#p.noFill();
    this.#p.strokeCap(this.#p.ROUND);
    this.#p.strokeJoin(this.#p.ROUND);

    ctx.shadowBlur = radius * 0.12;
    ctx.shadowColor = 'rgba(0,0,0,0.18)';
    this.#p.stroke(0x8A, 0x76, 0x50, 220);
    this.#p.strokeWeight(radius * 0.33);
    this.#p.beginShape();
    this.#p.curveVertex(first.x, first.y);
    this.#p.curveVertex(first.x, first.y);
    for (const point of points) {
      this.#p.curveVertex(point.x, point.y);
    }
    this.#p.curveVertex(last.x, last.y);
    this.#p.curveVertex(last.x, last.y);
    this.#p.endShape();

    ctx.shadowBlur = 0;
    ctx.shadowColor = 'rgba(0,0,0,0)';
    this.#p.stroke(0xC7, 0xB4, 0x8A, 205);
    this.#p.strokeWeight(radius * 0.18);
    this.#p.beginShape();
    this.#p.curveVertex(first.x, first.y);
    this.#p.curveVertex(first.x, first.y);
    for (const point of points) {
      this.#p.curveVertex(point.x, point.y);
    }
    this.#p.curveVertex(last.x, last.y);
    this.#p.curveVertex(last.x, last.y);
    this.#p.endShape();
    this.#p.pop();
  }
}
