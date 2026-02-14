export class RoadType {
  #name;
  #movementCost;

  constructor(name, movementCost) {
    this.#name = name;
    this.#movementCost = movementCost;
  }

  get name() {
    return this.#name;
  }

  get movementCost() {
    return this.#movementCost;
  }
}

export class Road {
  #type;
  #path;

  constructor(type, path) {
    this.#type = type;
    // Path coordinates are stored as an array of [row, column] pairs, e.g. [[5, 0], [5, 1], [6, 2]].
    this.#path = path;
  }

  get type() {
    return this.#type.name;
  }

  get path() {
    return this.#path;
  }

  get movementCost() {
    return this.#type.movementCost;
  }
}
