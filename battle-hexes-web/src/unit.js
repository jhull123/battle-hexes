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

  constructor(name, faction, type, attack, defense, move) {
    this.#name = name;
    this.#faction = faction;
    this.#type = type;
    this.#attack = attack;
    this.#defense = defense;
    this.#move = move;
    this.#movesRemaining = move;
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

    if (this.hasOpponentInAdjacentHex(adjacentHexes)) {
      this.#movesRemaining = 0; 
    } else if (this.#movesRemaining > 0) {
      this.#movesRemaining--;
    }
  }

  hasOpponentInAdjacentHex(adjacentHexes) {
    for (let adjacentHex of adjacentHexes) {
      let occupier = adjacentHex.getOccupier();
      if (occupier !== null && occupier !== this.#faction) {
        return true;
      }
    }

    return false;
  }

  getMovesRemaining() {
    return this.#movesRemaining;
  }

  resetMovesRemaining() {
    this.#movesRemaining = this.getMovement();
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
}
