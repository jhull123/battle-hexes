class SelectionDrawer {
  #hexDrawer;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
  }

  drawHexSelection(aHex) {
    if (aHex.isSelected()) {
      this.#hexDrawer.drawHex(aHex, '#10C010', 6);
    } else if (aHex.isMoveTarget()) {
      this.#hexDrawer.drawHex(aHex, '#10F010', 6);
    }
  }
}