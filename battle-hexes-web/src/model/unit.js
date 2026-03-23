export class Unit {
  #movePath = [];
  #containingHex = undefined;
  #id;
  #name;
  #faction;
  #type;
  #attack;
  #echelon;
  #defense;
  #move;
  #movesRemaining;
  #combatOpponents;
  #defensiveFireAvailable;

  constructor(
    id,
    name,
    faction,
    type,
    attack,
    defense,
    move,
    echelon = null,
    defensiveFireAvailable = true,
  ) {
    this.#id = id;
    this.#name = name;
    this.#faction = faction;
    this.#type = type;
    this.#attack = attack;
    this.#echelon = echelon;
    this.#defense = defense;
    this.#move = move;
    this.#movesRemaining = move;
    this.#combatOpponents = [];
    this.#defensiveFireAvailable = defensiveFireAvailable;
  }

  toString() {
    return `${this.#name} (${this.#faction.getName()})`
  }

  getId() { return this.#id; }
  getName() { return this.#name; }
  getFaction() { return this.#faction; }
  getOwningPlayer() { return this.#faction?.getOwningPlayer?.(); }
  getType() { return this.#type; }
  getContainingHex() { return this.#containingHex; }
  setContainingHex(aHex) { this.#containingHex = aHex; }
  addToMovePath(hexToMoveTo) { this.#movePath.push(hexToMoveTo); }
  getMovePath() { return this.#movePath; }
  hasMovePath() { return this.#movePath.length > 0; }

  move(destinationHex, adjacentHexes) {
    if (this.#movesRemaining <= 0) {
      throw new Error('No movement points remaining!');
    }

    this.setContainingHex(destinationHex);
    this.updateCombatOpponents(adjacentHexes);

    if (this.#combatOpponents.length > 0) {
      this.#movesRemaining = 0;
      this.#defensiveFireAvailable = false;
      return;
    }

    const terrainMoveCost = destinationHex?.getTerrain()?.moveCost;
    const moveCost = Number.isFinite(terrainMoveCost) && terrainMoveCost > 0
      ? terrainMoveCost
      : 1;

    this.#movesRemaining = Math.max(0, this.#movesRemaining - moveCost);
    if (this.#movesRemaining <= 1) {
      this.#defensiveFireAvailable = false;
    }
  }

  updateCombatOpponents(adjacentHexes) {
    this.#combatOpponents = [];
    for (let adjacentHex of adjacentHexes) {
      let occupiers = adjacentHex.getOccupiers();
      if (occupiers.length > 0 && occupiers[0].getOwningPlayer() !== this.getOwningPlayer()) {
        this.#combatOpponents.push(occupiers);
        for (let occupier of occupiers) {
          occupier.#combatOpponents.push(this.#containingHex.getUnits());
        }
      }
    }
  }

  getMovesRemaining() { return this.#movesRemaining; }

  createMovementSnapshot() {
    return {
      containingHex: this.#containingHex,
      movesRemaining: this.#movesRemaining,
      defensiveFireAvailable: this.#defensiveFireAvailable,
    };
  }

  restoreMovementSnapshot(snapshot) {
    this.#containingHex = snapshot.containingHex;
    this.#movesRemaining = snapshot.movesRemaining;
    this.#defensiveFireAvailable = snapshot.defensiveFireAvailable;
    this.#combatOpponents = [];
  }

  canEnterHex(destinationHex) {
    const terrainMoveCost = destinationHex?.getTerrain()?.moveCost;
    const moveCost = Number.isFinite(terrainMoveCost) && terrainMoveCost > 0
      ? terrainMoveCost
      : 1;
    return this.getMovesRemaining() >= moveCost;
  }

  resetMovesRemaining() {
    this.#movesRemaining = this.getMovement();
  }

  resetDefensiveFire() {
    this.#defensiveFireAvailable = true;
  }

  resetCombat() { this.#combatOpponents = []; }
  getMovement() { return this.#move; }
  getEchelon() { return this.#echelon; }
  getDefense() { return this.#defense; }
  getAttack() { return this.#attack; }

  hasDefensiveFire() {
    return this.#defensiveFireAvailable;
  }

  setDefensiveFireAvailable(isAvailable) {
    this.#defensiveFireAvailable = !!isAvailable;
  }

  isMovable() {
    return this.getMovesRemaining() > 0 && this.getOwningPlayer().isHuman();
  }

  getCombatOpponents() { return this.#combatOpponents; }
  isOwnedBy(player) { return this.getOwningPlayer() == player; }
}
