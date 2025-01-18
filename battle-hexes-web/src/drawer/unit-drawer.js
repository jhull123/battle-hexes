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
    // this.#p.stroke(96, 32, 32);
    this.#p.stroke(this.#halfColor(aUnit.getFaction().getCounterColor()));
    this.#p.strokeWeight(3);
    // this.#p.fill(200, 16, 16);
    this.#p.fill(aUnit.getFaction().getCounterColor());

    this.#p.rectMode(this.#p.CENTER);
    this.#p.rect(x, y, this.#counterSide, this.#counterSide, 3);

    this.#drawInfantrySymbol(x, y, this.#counterSide / 2, this.#counterSideThird);
    this.#drawUnitStats(aUnit, x, y);
    this.#drawUnitSize(x, y);
  }

  #halfColor(hexColor) {
    // Ensure the hex color starts with a "#"
    if (hexColor[0] === '#') {
      hexColor = hexColor.slice(1);
    }

    // Parse the color into RGB components
    let r = parseInt(hexColor.substring(0, 2), 16);
    let g = parseInt(hexColor.substring(2, 4), 16);
    let b = parseInt(hexColor.substring(4, 6), 16);

    // Divide each color component by 2 and ensure it doesn't go below 0
    r = Math.floor(r / 2);
    g = Math.floor(g / 2);
    b = Math.floor(b / 2);

    // Convert back to a hex string and pad if necessary
    const halfHexColor = `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    return halfHexColor;
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