import { Battle } from "./model/battle";

export class Combat {
  #units;
  #attackingPlayer;
  
  constructor(units, attackingPlayer) {
    this.#units = units;
    this.#attackingPlayer = attackingPlayer;
  }

  hasCombat() {
    for (let unit of this.#units) {
      if (unit.getContainingHex().hasCombat()) {
        return true;
      }
    }
    return false;
  }

  getBattles() {
    const battles = [];
    
    for (let unit of this.#units) {
      if (unit.isOwnedBy(this.#attackingPlayer)) {
        continue;
      }

      const combatOpponents = this.#getOpponents(unit);
      if (combatOpponents.length === 0) {
        continue;
      }

      const battle = new Battle();
      battle.addDefendingUnit(unit);
      for (let attaker of combatOpponents) {
        battle.addAttackingUnit(attaker);
      }

      if (!battle.isEmpty()) {
        battles.push(battle);
      }
    }

    return battles;
  }

  #getOpponents(defendingUnit) {
    const opponents = new Set();

    for (let unit of this.#units) {
      if (unit.isOwnedBy(defendingUnit.getOwningPlayer())) {
        continue;
      }

      if (defendingUnit.getContainingHex().isAdjacent(unit.getContainingHex())) {
        opponents.add(unit);
      }
    }

    return opponents;
  }
}