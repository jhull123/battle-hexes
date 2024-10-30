export class UnitDrawer {
  #p;
  #hexDrawer;
  #counterSide;
  #counterSideThird;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
    this.#counterSide = hexDrawer.getHexRadius() + hexDrawer.getHexRadius() * 0.3;
    this.#counterSideThird = this.#counterSide / 3;
  }

  draw(aHex) {
    let hexCenter = this.#hexDrawer.hexCenter(aHex);
    for (let aUnit of aHex.getUnits()) {
      this.drawCounter(aUnit, hexCenter.x, hexCenter.y);
    }
  }

  /* x and y are the center of the square. side is the square side length. */
  drawCounter(aUnit, x, y) {
    this.#p.stroke(96, 32, 32);
    this.#p.strokeWeight(3);
    this.#p.fill(200, 16, 16);

    this.#p.rectMode(this.#p.CENTER);
    this.#p.rect(x, y, this.#counterSide, this.#counterSide, 3);

    this.#drawInfantrySymbol(x, y, this.#counterSide / 2, this.#counterSideThird);
    this.#drawUnitStats(aUnit, x, y);
    this.#drawUnitSize(x, y);
  }

  #drawInfantrySymbol(x, y, width, height) {
    this.#p.stroke(255)
    this.#p.strokeWeight(2);
    this.#p.rect(x, y, width, height);
  
    let halfWidth = width / 2;
    let halfHeight = height / 2;
  
    this.#p.stroke(255);
    this.#p.strokeWeight(2);
  
    // Draw "X" by connecting the corners of the smaller rectangle
    this.#p.line(x - halfWidth, y - halfHeight, x + halfWidth, y + halfHeight);
    this.#p.line(x + halfWidth, y - halfHeight, x - halfWidth, y + halfHeight);
  }
  
  #drawUnitStats(aUnit, x, y) {
    this.#p.fill(255);
    this.#p.noStroke();
    this.#p.textSize(14);
    this.#p.textAlign(this.#p.CENTER, this.#p.CENTER);    
    this.#p.text(`${aUnit.getAttack()}-${aUnit.getDefense()}-${aUnit.getMovement()}`, x, y + this.#counterSideThird);
  }
  
  #drawUnitSize(x, y) {
    this.#p.fill(255);
    this.#p.noStroke();
    this.#p.textSize(9);
    this.#p.textAlign(this.#p.CENTER, this.#p.CENTER);
    this.#p.text('XX', x, y - this.#counterSideThird + this.#counterSideThird * 0.2);
  }  
}