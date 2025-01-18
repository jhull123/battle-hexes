export class MoveArrowDrawer {
  #p;
  #hexDrawer;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    if (!aHex.isEmpty() && aHex.getUnits()[0].hasMovePath()) {
      const movePath = aHex.getUnits()[0].getMovePath();
      this.#drawMoveArrow(movePath[0], movePath[1]);
    } else if (aHex.getMoveHoverFromHex() && aHex.getMoveHoverFromHex().getUnits()[0].isMovable()) {
      console.log('Lets draw a move arrow!');
      this.#drawMoveArrow(aHex.getMoveHoverFromHex(), aHex);
    }
  }

  #drawMoveArrow(fromHex, toHex) {
    this.#p.stroke(0, 208, 0);
    this.#p.strokeWeight(2);
    this.#p.fill(16, 240, 16);
  
    let toCenter = this.#hexDrawer.hexCenter(toHex);
    let fromCenter = this.#hexDrawer.hexCenter(fromHex);
  
    let angle = this.#p.atan2(toCenter.y - fromCenter.y, toCenter.x - fromCenter.x) + 0.5 * this.#p.PI;
  
    const hexRadius = this.#hexDrawer.getHexRadius();
    let arrowLength = hexRadius;
    let arrowWidth = hexRadius / 2;
    let arrowTop = -0.75 * hexRadius * 2;
  
    this.#p.push();
    this.#p.translate(fromCenter.x, fromCenter.y);
    this.#p.rotate(angle);
  
    this.#p.beginShape();
    this.#p.vertex(0, arrowTop); // top of the arrow
    this.#p.vertex(-arrowWidth / 2, arrowTop + arrowLength / 3);  // Left side 1
    this.#p.vertex(-arrowWidth / 4, arrowTop + arrowLength / 3);  // Left side 2
    this.#p.vertex(-arrowWidth / 4, arrowTop + arrowLength);      // Left side 3
    this.#p.vertex(arrowWidth / 4, arrowTop + arrowLength);       // Right side 3
    this.#p.vertex(arrowWidth / 4, arrowTop + arrowLength / 3);   // Right side 2
    this.#p.vertex(arrowWidth / 2, arrowTop + arrowLength / 3);   // Right side 1
    this.#p.endShape(this.#p.CLOSE);
  
    this.#p.pop();
  }
}
