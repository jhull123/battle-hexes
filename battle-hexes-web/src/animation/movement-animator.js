import { eventBus } from '../event-bus.js';

export class MovementAnimator {
  #board;
  #delay;

  constructor(board, delay = 300) {
    this.#board = board;
    this.#delay = delay;
  }

  async animate(unit, path, adjustMoves = false) {
    if (!unit || !path || path.length < 2) {
      return;
    }

    let prevHex = path[0];
    for (let i = 1; i < path.length; i++) {
      const nextHex = path[i];
      this.#board.updateUnitPosition(unit, prevHex, nextHex);
      eventBus.emit('redraw');
      await new Promise(resolve => setTimeout(resolve, this.#delay));
      prevHex = nextHex;
    }

    if (adjustMoves) {
      unit.move(prevHex, this.#board.getAdjacentHexes(prevHex));
    }
    this.#board.refreshCombat();
    eventBus.emit('menuUpdate');
  }
}
