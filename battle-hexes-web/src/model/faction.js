import { Utils } from './utils.js';

export class Faction {
  #id;
  #name;
  #counterColor;
  #owningPlayer;
  #sounds;

  constructor(id, name, counterColor, sounds = {}) {
    this.#id = id;
    this.#name = name;
    this.#counterColor = counterColor;
    this.#sounds = Utils.cloneValue(sounds) ?? {};
  }

  setOwningPlayer(player) {
    this.#owningPlayer = player;
  }

  getId() {
    return this.#id;
  }

  getName() {
    return this.#name;
  }

  getCounterColor() {
    return this.#counterColor;
  }

  getOwningPlayer() {
    return this.#owningPlayer;
  }

  getSounds() {
    return Utils.cloneValue(this.#sounds) ?? {};
  }

  toString() {
    return this.#name;
  }
}
