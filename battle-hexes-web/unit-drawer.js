class UnitDrawer {
  #hexDrawer;
  #counterSide;
  #counterSideThird;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
    this.#counterSide = hexRadius + hexRadius * 0.3;
    this.#counterSideThird = counterSide / 3;
  }

  drawHexCounters(aHex) {
    let hexCenter = this.#hexDrawer.hexCenter(aHex);
    for (let aUnit of aHex.getUnits()) {
      this.drawCounter(hexCenter.x, hexCenter.y);
    }
  }

  /* x and y are the center of the square. side is the square side length. */
  drawCounter(x, y) {
    stroke(96, 32, 32);
    strokeWeight(3);
    fill(200, 16, 16);

    rectMode(CENTER);
    rect(x, y, this.#counterSide, this.#counterSide, 3);

    this.#drawInfantrySymbol(x, y, this.#counterSide / 2, this.#counterSideThird);
    this.#drawUnitStats(x, y);
    this.#drawUnitSize(x, y);
  }

  #drawInfantrySymbol(x, y, width, height) {
    stroke(255)
    strokeWeight(2);
    rect(x, y, width, height);
  
    let halfWidth = width / 2;
    let halfHeight = height / 2;
  
    stroke(255);
    strokeWeight(2);
  
    // Draw "X" by connecting the corners of the smaller rectangle
    line(x - halfWidth, y - halfHeight, x + halfWidth, y + halfHeight);
    line(x + halfWidth, y - halfHeight, x - halfWidth, y + halfHeight);
  }
  
  #drawUnitStats(x, y) {
    fill(255);
    noStroke();
    textSize(14);
    textAlign(CENTER, CENTER);    
    text('4-4-4', x, y + this.#counterSideThird);
  }
  
  #drawUnitSize(x, y) {
    fill(255);
    noStroke();
    textSize(9);
    textAlign(CENTER, CENTER);
    text('XX', x, y - this.#counterSideThird + this.#counterSideThird * 0.2);
  }  
}