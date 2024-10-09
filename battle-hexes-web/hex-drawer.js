class HexDrawer {
  #hexRadius;
  #hexHeight;
  #hexDiameter;
  #showHexCoords;
  
  constructor(hexRadius) {
    this.#hexRadius = hexRadius;
    this.#hexHeight = Math.sqrt(3) * hexRadius;
    this.#hexDiameter = hexRadius * 2;
    
    this.#showHexCoords = false;
  }

  draw(hexToDraw) {
    this.drawHex(hexToDraw, '#202020', 2, '#fffdd0');
  }

  drawHex(hexToDraw, strokeColor, strokeSize, fillColor) {
    let hexCenter = this.hexCenter(hexToDraw);
    stroke(strokeColor);
    strokeWeight(strokeSize);

    if (fillColor) {
      fill(fillColor);
    } else {
      noFill();
    }

    beginShape();
    for (let i = 0; i < 6; i++) {
      let angle = TWO_PI / 6 * i;
      let vx = hexCenter.x + cos(angle) * this.#hexRadius;
      let vy = hexCenter.y + sin(angle) * this.#hexRadius;
      vertex(vx, vy);
    }
    endShape(CLOSE);

    if (this.#showHexCoords) {
      this.#drawHexCoords(hexToDraw, hexCenter);
    }
  }

  #drawHexCoords(hexToDraw, hexPosition) {
    fill(0);
    noStroke();  // No outline for the text
    textSize(16);
    textAlign(CENTER, CENTER);  // Center align text horizontally and vertically    
    text(`${hexToDraw.row}, ${hexToDraw.column}`, hexPosition.x, hexPosition.y);  
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