class SelectionDrawer {
  #hexDrawer;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    if (aHex.isSelected()) {
      this.#hexDrawer.drawHex(aHex, '#10C010', 6);
    } else if (aHex.isMoveHover()) {
      console.log('drawing move hover selection ' + aHex);
      this.#hexDrawer.drawHex(aHex, '#10F010', 6);
    }
  }
}