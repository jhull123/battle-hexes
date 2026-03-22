import { eventBus } from '../event-bus.js';

export class MovementAnimator {
  #board;
  #delay;
  #animationToken;

  constructor(board, delay = 200) {
    this.#board = board;
    this.#delay = delay;
    this.#animationToken = null;
  }

  stop() {
    if (this.#animationToken) {
      this.#animationToken.cancelled = true;
      this.#animationToken = null;
    }
  }

  async animate(unit, path, adjustMoves = false) {
    if (!unit || !path || path.length < 2) {
      return;
    }

    const animationToken = { cancelled: false };
    this.#animationToken = animationToken;
    let prevHex = path[0];
    for (let i = 1; i < path.length; i++) {
      if (animationToken.cancelled) {
        return;
      }
      const nextHex = path[i];
      this.#board.updateUnitPosition(unit, prevHex, nextHex);
      eventBus.emit('redraw');
      await new Promise(resolve => setTimeout(resolve, this.#delay));
      if (animationToken.cancelled) {
        return;
      }
      prevHex = nextHex;
    }

    if (adjustMoves) {
      unit.move(prevHex, this.#board.getAdjacentHexes(prevHex));
    }
    this.#animationToken = null;
    this.#board.refreshCombat();
    eventBus.emit('redraw');
    eventBus.emit('menuUpdate');
  }
}
