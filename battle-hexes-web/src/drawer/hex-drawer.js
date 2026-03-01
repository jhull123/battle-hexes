export class HexDrawer {
  #p;
  #hexRadius;
  #hexHeight;
  #hexDiameter;
  #showHexCoords;

  constructor(p, hexRadius) {
    this.#p = p;
    this.#hexRadius = hexRadius;
    this.#hexHeight = Math.sqrt(3) * hexRadius;
    this.#hexDiameter = hexRadius * 2;

    this.#showHexCoords = false;
  }

  draw(hexToDraw) {
    const terrain = hexToDraw.getTerrain();
    const fillColor = terrain ? terrain.color : '#fffdd0';
    this.drawHex(hexToDraw, '#202020', 2, fillColor);
  }

  drawHex(hexToDraw, strokeColor, strokeSize, fillColor) {
    const vertices = this.getHexVertices(hexToDraw);
    const hexCenter = this.hexCenter(hexToDraw);

    this.#p.stroke(strokeColor);
    this.#p.strokeWeight(strokeSize);

    if (fillColor) {
      this.#p.fill(fillColor);
    } else {
      this.#p.noFill();
    }

    this.#p.beginShape();
    vertices.forEach(({ x, y }) => this.#p.vertex(x, y));
    this.#p.endShape(this.#p.CLOSE);

    if (this.#showHexCoords) {
      this.#drawHexCoords(hexToDraw, hexCenter);
    }
  }

  #drawHexCoords(hexToDraw, hexPosition) {
    this.#p.fill(0);
    this.#p.noStroke();
    this.#p.textSize(16);
    this.#p.textAlign(this.#p.CENTER, this.#p.CENTER);
    this.#p.text(`${hexToDraw.row}, ${hexToDraw.column}`, hexPosition.x, hexPosition.y);
  }

  hexCenter(hexToDraw) {
    const oddColumnOffsetX = (hexToDraw.column * this.#hexRadius) / 2;
    const oddColumnOffsetY = hexToDraw.column % 2 === 0 ? 0 : this.#hexHeight / 2;

    const x = this.#hexRadius + hexToDraw.column * this.#hexDiameter - oddColumnOffsetX;
    const y = this.#hexHeight / 2 + hexToDraw.row * this.#hexHeight + oddColumnOffsetY;

    return { x, y };
  }

  getHexVertices(hexToDraw, radius = this.#hexRadius) {
    const hexCenter = this.hexCenter(hexToDraw);
    const vertices = [];

    for (let i = 0; i < 6; i += 1) {
      const angle = (this.#p.TWO_PI / 6) * i;
      vertices.push({
        x: hexCenter.x + this.#p.cos(angle) * radius,
        y: hexCenter.y + this.#p.sin(angle) * radius,
      });
    }

    return vertices;
  }

  setShowHexCoords(showOrNot) {
    this.#showHexCoords = showOrNot;
  }

  getHexRadius() {
    return this.#hexRadius;
  }
}
