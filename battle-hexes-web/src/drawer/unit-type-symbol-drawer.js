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

    if (normalizedUnitType === 'parachute infantry') {
      this.#drawAirborneInfantrySymbol(x, y, width, height);
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

    const trackWidth = width * 0.7;
    const trackHeight = height * 0.4;
    const cornerRadius = trackHeight / 2;

    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.noFill();
    this.#p.rect(x, y, trackWidth, trackHeight, cornerRadius);
  }

  #drawAirborneInfantrySymbol(x, y, width, height) {
    this.#drawInfantrySymbol(x, y, width, height);

    const canopyWidth = width * 0.4;
    const canopyHeight = height * 0.16;
    const canopyCenterY = y - (height / 2) + (height * 0.68);
    const canopyBaseY = canopyCenterY + (canopyHeight / 2);
    const suspensionBottomY = canopyBaseY + (height * 0.1);

    this.#p.noFill();
    this.#p.arc(x, canopyCenterY, canopyWidth, canopyHeight * 2, this.#p.PI, this.#p.TWO_PI);
    this.#p.line(x - (canopyWidth * 0.25), canopyBaseY, x, suspensionBottomY);
    this.#p.line(x + (canopyWidth * 0.25), canopyBaseY, x, suspensionBottomY);
  }

  #drawFallbackUnitTypeSymbol(x, y, width, height) {
    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.rect(x, y, width, height);
  }
}
