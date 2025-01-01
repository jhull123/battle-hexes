export class Battle {
  #attackingUnits = new Set();
  #defendingUnits = new Set();
  
  addAttackingUnit(attackingUnit) {
    this.#attackingUnits.add(attackingUnit);
  }

  addDefendingUnit(defendingUnit) {
    this.#defendingUnits.add(defendingUnit);
  }

  getAttackingUnits() {
    return this.#attackingUnits;
  }

  getDefendingUnits() {
    return this.#defendingUnits;
  }

  isEmpty() {
    return this.#attackingUnits.size === 0 || this.#defendingUnits.size === 0;
  }
}