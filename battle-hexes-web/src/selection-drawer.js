export class SelectionDrawer {
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

export class MoveSelectionDrawer {
  #hexDrawer;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    if (aHex.getMoveHoverFromHex() && aHex.getMoveHoverFromHex().getUnits()[0].isMovable()) {
      // console.log('drawing move hover selection ' + aHex);
      this.#hexDrawer.drawHex(aHex, '#10F010', 6);
    }
  }
}

export class CombatSelectionDrawer {
  #hexDrawer;

  constructor(hexDrawer) {
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    if (aHex.hasCombat()) {
      this.#hexDrawer.drawHex(aHex, '#FF1010', 2);
    }
  }
}