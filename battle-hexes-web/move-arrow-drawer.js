class MoveArrowDrawer {
  #hexDrawer;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    if (!aHex.isEmpty() && aHex.getUnits()[0].hasMovePath()) {
      const movePath = aHex.getUnits()[0].getMovePath();
      this.#drawMoveArrow(movePath[0], movePath[1]);
    } else if (aHex.getMoveHoverFromHex()) {
      console.log('Lets draw a move arrow!');
      this.#drawMoveArrow(aHex.getMoveHoverFromHex(), aHex);
    }
  }

  #drawMoveArrow(fromHex, toHex) {
    stroke(0, 208, 0);
    strokeWeight(2);
    fill(16, 240, 16);
  
    let toCenter = this.#hexDrawer.hexCenter(toHex);
    let fromCenter = this.#hexDrawer.hexCenter(fromHex);
  
    let angle = atan2(toCenter.y - fromCenter.y, toCenter.x - fromCenter.x) + 0.5 * PI;
  
    let arrowLength = hexRadius;
    let arrowWidth = hexRadius / 2;
    let arrowTop = -0.75 * hexDiameter;
  
    push();
    translate(fromCenter.x, fromCenter.y);
    rotate(angle);
  
    beginShape();
    vertex(0, arrowTop); // top of the arrow
    vertex(-arrowWidth / 2, arrowTop + arrowLength / 3);  // Left side 1
    vertex(-arrowWidth / 4, arrowTop + arrowLength / 3);  // Left side 2
    vertex(-arrowWidth / 4, arrowTop + arrowLength);      // Left side 3
    vertex(arrowWidth / 4, arrowTop + arrowLength);       // Right side 3
    vertex(arrowWidth / 4, arrowTop + arrowLength / 3);   // Right side 2
    vertex(arrowWidth / 2, arrowTop + arrowLength / 3);   // Right side 1
    endShape(CLOSE);
  
    pop();
  }
}
