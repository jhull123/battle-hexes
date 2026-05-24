export class UnitTypeSymbolDrawer {
  #p;

  constructor(p) {
    this.#p = p;
  }

  draw(aUnit, x, y, width, height) {
    const unitType = aUnit.getType?.();
    const normalizedUnitType = unitType?.trim().toLowerCase();

    if (normalizedUnitType === 'infantry') {
      this.#drawInfantrySymbol(x, y, width, height);
      return;
    }

    if (normalizedUnitType === 'armor') {
      this.#drawArmorSymbol(x, y, width, height);
      return;
    }

    this.#drawFallbackUnitTypeSymbol(x, y, width, height);
  }

  #drawInfantrySymbol(x, y, width, height) {
    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.rect(x, y, width, height);

    const halfWidth = width / 2;
    const halfHeight = height / 2;

    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.line(x - halfWidth, y - halfHeight, x + halfWidth, y + halfHeight);
    this.#p.line(x + halfWidth, y - halfHeight, x - halfWidth, y + halfHeight);
  }

  #drawArmorSymbol(x, y, width, height) {
    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.rect(x, y, width, height);

    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.ellipse(x, y, width, height);
  }

  #drawFallbackUnitTypeSymbol(x, y, width, height) {
    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.rect(x, y, width, height);
  }
}
