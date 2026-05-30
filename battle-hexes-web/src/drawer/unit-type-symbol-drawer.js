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

    if (normalizedUnitType === 'mg' || normalizedUnitType === 'machine gun') {
      this.#drawMachineGunSymbol(x, y, width, height);
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

    const markerWidth = width * 0.3;
    const humpWidth = markerWidth / 1.8;
    const humpHeight = height * 0.23;
    const markerCenterY = y + (height * 0.36);
    const leftHumpCenterX = x - (humpWidth / 2);
    const rightHumpCenterX = x + (humpWidth / 2);

    this.#p.stroke(255);
    this.#p.strokeWeight(0.9);
    this.#p.noFill();
    this.#p.arc(leftHumpCenterX, markerCenterY, humpWidth, humpHeight, this.#p.PI, this.#p.TWO_PI);
    this.#p.arc(rightHumpCenterX, markerCenterY, humpWidth, humpHeight, this.#p.PI, this.#p.TWO_PI);
    this.#p.strokeWeight(2);
  }

  #drawMachineGunSymbol(x, y, width, height) {
    this.#drawInfantrySymbol(x, y, width, height);

    const barWidth = width * 0.38;
    const barY = y + (height * 0.25);
    const barHalfWidth = barWidth / 2;

    this.#p.stroke(255);
    this.#p.strokeWeight(1.25);
    this.#p.line(x - barHalfWidth, barY, x + barHalfWidth, barY);
    this.#p.strokeWeight(2);
  }

  #drawFallbackUnitTypeSymbol(x, y, width, height) {
    this.#p.stroke(255);
    this.#p.strokeWeight(2);
    this.#p.rect(x, y, width, height);
  }
}
