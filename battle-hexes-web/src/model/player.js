export class Player {
  #name;
  #type;
  #factions;

  constructor(name, type, factions) {
    this.#name = name;
    this.#type = type;
    this.#factions = factions;
  }

  getName() {
    return this.#name;
  }

  getType() {
    return this.#type;
  }

  getFactions() {
    return this.#factions;
  }
}

export const playerTypes = {
  HUMAN: 'Human',
  CPU: 'Computer'
};
