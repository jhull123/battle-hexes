import { playerTypes } from "./faction.js";

export class Unit {
  #movePath = [];
  #containingHex = undefined;
  #name;
  #faction;
  #type;
  #attack;
  #defense;
  #move;
  #movesRemaining;
  #combatOpponents;

  constructor(name, faction, type, attack, defense, move) {
    this.#name = name;
    this.#faction = faction;
    this.#type = type;
    this.#attack = attack;
    this.#defense = defense;
    this.#move = move;
    this.#movesRemaining = move;
    this.#combatOpponents = [];
  }

  toString() {
    return `${this.#name} (${this.#faction.getName()})`
  }

  getName() {
    return this.#name;
  }

  getFaction() {
    return this.#faction;
  }

  getType() {
    return this.#type;
  }

  getContainingHex() {
    return this.#containingHex;
  }

  setContainingHex(aHex) {
    this.#containingHex = aHex;
  }

  addToMovePath(hexToMoveTo) {
    this.#movePath.push(hexToMoveTo);
  }

  getMovePath() {
    return this.#movePath;
  }

  hasMovePath() {
    return this.#movePath.length > 0;
  }

  move(destinationHex, adjacentHexes) {
    if (this.#movesRemaining <= 0) {
      throw new Error('No movement points remaining!');
    }

    this.setContainingHex(destinationHex);
    this.updateCombatOpponents(adjacentHexes);

    if (this.#combatOpponents.length > 0) {
      this.#movesRemaining = 0; 
    } else if (this.#movesRemaining > 0) {
      this.#movesRemaining--;
    }
  }

  updateCombatOpponents(adjacentHexes) {
    for (let adjacentHex of adjacentHexes) {
      let occupiers = adjacentHex.getOccupiers();
      if (occupiers.length > 0 && occupiers[0].getFaction() !== this.#faction) {
        this.#combatOpponents.push(occupiers);
        for (let occupier of occupiers) {
          occupier.#combatOpponents.push(this.#containingHex.getUnits());
        }
      }
    }
  }

  getMovesRemaining() {
    return this.#movesRemaining;
  }

  resetMovesRemaining() {
    this.#movesRemaining = this.getMovement();
  }

  resetCombat() {
    this.#combatOpponents = [];
  }

  getMovement() {
    return this.#move;
  }

  getDefense() {
    return this.#defense;
  }

  getAttack() {
    return this.#attack;
  }

  isMovable() {
    return this.#faction.getPlayerType() === playerTypes.HUMAN && this.getMovesRemaining() > 0; 
  }

  getCombatOpponents() {
    return this.#combatOpponents;
  }
}
