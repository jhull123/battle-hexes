class SelectionDrawer {
  #hexDrawer;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    if (aHex.isSelected()) {
      this.#hexDrawer.drawHex(aHex, '#10C010', 6);
    }
  }
}

class MoveSelectionDrawer {
  #hexDrawer;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    if (aHex.getMoveHoverFromHex() && aHex.getMoveHoverFromHex().getUnits()[0].getMovesRemaining() > 0) {
      // console.log('drawing move hover selection ' + aHex);
      this.#hexDrawer.drawHex(aHex, '#10F010', 6);
    }
  }
}