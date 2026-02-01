import { TerrainDrawerResolver } from "../terraindraw/terrain-drawer-resolver.js";

export class HexDrawer {
  #p;
  #hexRadius;
  #hexHeight;
  #hexDiameter;
  #showHexCoords;
  #terrainDrawerResolver;

  constructor(p, hexRadius) {
    this.#p = p;
    this.#hexRadius = hexRadius;
    this.#hexHeight = Math.sqrt(3) * hexRadius;
    this.#hexDiameter = hexRadius * 2;
    
    this.#showHexCoords = false;
    this.#terrainDrawerResolver = new TerrainDrawerResolver(p, this);
  }

  draw(hexToDraw) {
    const terrain = hexToDraw.getTerrain();
    const fillColor = terrain ? terrain.getColor() : '#fffdd0';
    this.drawHex(hexToDraw, '#202020', 2, fillColor);
    this.#terrainDrawerResolver.resolve(hexToDraw)?.draw(hexToDraw);
  }

  drawHex(hexToDraw, strokeColor, strokeSize, fillColor) {
    let hexCenter = this.hexCenter(hexToDraw);
    this.#p.stroke(strokeColor);
    this.#p.strokeWeight(strokeSize);

    if (fillColor) {
      this.#p.fill(fillColor);
    } else {
      this.#p.noFill();
    }

    this.#p.beginShape();
    for (let i = 0; i < 6; i++) {
      let angle = this.#p.TWO_PI / 6 * i;
      let vx = hexCenter.x + this.#p.cos(angle) * this.#hexRadius;
      let vy = hexCenter.y + this.#p.sin(angle) * this.#hexRadius;
      this.#p.vertex(vx, vy);
    }
    this.#p.endShape(this.#p.CLOSE);

    if (this.#showHexCoords) {
      this.#drawHexCoords(hexToDraw, hexCenter);
    }
  }

  #drawHexCoords(hexToDraw, hexPosition) {
    this.#p.fill(0);
    this.#p.noStroke();  // No outline for the text
    this.#p.textSize(16);
    this.#p.textAlign(this.#p.CENTER, this.#p.CENTER);  // Center align text horizontally and vertically    
    this.#p.text(`${hexToDraw.row}, ${hexToDraw.column}`, hexPosition.x, hexPosition.y);  
  }

  hexCenter(hexToDraw) {
    let oddColumnOffsetX = hexToDraw.column * this.#hexRadius / 2;
    let oddColumnOffsetY = hexToDraw.column % 2 == 0 ? 0 : this.#hexHeight / 2;

    let x = this.#hexRadius + hexToDraw.column * this.#hexDiameter - oddColumnOffsetX;
    let y = this.#hexHeight / 2 + hexToDraw.row * this.#hexHeight + oddColumnOffsetY;

    return {x, y};
  }

  setShowHexCoords(showOrNot) {
    this.#showHexCoords = showOrNot;
  }

  getHexRadius() {
    return this.#hexRadius;
  }
}