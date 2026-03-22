import { eventBus } from '../event-bus.js';

export class MovementAnimator {
  #board;
  #delay;
  #activeAnimations;

  constructor(board, delay = 200) {
    this.#board = board;
    this.#delay = delay;
    this.#activeAnimations = new Map();
  }

  async animate(unit, path, adjustMoves = false) {
    if (!unit || !path || path.length < 2) {
      return;
    }

    const token = { cancelled: false };
    const key = unit.getId?.() ?? unit;
    this.#activeAnimations.set(key, token);

    try {
      let prevHex = path[0];
      for (let i = 1; i < path.length; i++) {
        if (token.cancelled) {
          return;
        }

        const nextHex = path[i];
        this.#board.updateUnitPosition(unit, prevHex, nextHex);
        eventBus.emit('redraw');
        await new Promise(resolve => setTimeout(resolve, this.#delay));
        prevHex = nextHex;
      }

      if (token.cancelled) {
        return;
      }

      if (adjustMoves) {
        unit.move(prevHex, this.#board.getAdjacentHexes(prevHex));
      }
      this.#board.refreshCombat();
      eventBus.emit('redraw');
      eventBus.emit('menuUpdate');
    } finally {
      this.#activeAnimations.delete(key);
    }
  }

  interrupt(unitOrId) {
    const key = unitOrId?.getId?.() ?? unitOrId;
    const token = this.#activeAnimations.get(key);
    if (!token) {
      return false;
    }

    token.cancelled = true;
    this.#activeAnimations.delete(key);
    return true;
  }
}
