export class Terrain {
  #name;
  #color;
  #moveCost;
  #combatOddsShift;

  constructor(name, color, moveCost = 1, combatOddsShift = 0) {
    this.#name = name;
    this.#color = color;
    this.#moveCost = Number.isFinite(moveCost) && moveCost > 0 ? moveCost : 1;
    this.#combatOddsShift = Number.isFinite(combatOddsShift) ? combatOddsShift : 0;
  }

  get name() {
    return this.#name;
  }

  get color() {
    return this.#color;
  }

  get moveCost() {
    return this.#moveCost;
  }

  get combatOddsShift() {
    return this.#combatOddsShift;
  }
}
