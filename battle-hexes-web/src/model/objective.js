export class Objective {
  #type;
  #points;

  constructor(type, points) {
    this.#type = type;
    this.#points = points;
    Object.freeze(this);
  }

  get type() {
    return this.#type;
  }

  get points() {
    return this.#points;
  }

  get displayName() {
    if (!this.#type) {
      return '';
    }
    return this.#type.charAt(0).toUpperCase() + this.#type.slice(1);
  }
}
