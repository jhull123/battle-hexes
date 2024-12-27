export class Combat {
  #units;
  
  constructor(units) {
    this.#units = units;
  }

  hasCombat() {
    for (let unit of this.#units) {
      if (unit.getContainingHex().hasCombat()) {
        return true;
      }
    }
    return false;
  }
}