import { BoardUpdater } from './board-updater.js';

export class MovementResponseHandler {
  #boardUpdater;

  constructor(boardUpdater = new BoardUpdater()) {
    this.#boardUpdater = boardUpdater;
  }

  apply(game, responseData = {}) {
    game.updateScores?.(responseData?.scores);
    game.updateTurnState?.({
      turnLimit: responseData?.turnLimit,
      turnNumber: responseData?.turnNumber,
    });

    const units = this.#getUnits(responseData);
    if (units) {
      this.#boardUpdater.updateBoard(game.getBoard(), units, {
        defensiveFireEvents: this.#getDefensiveFireEvents(responseData),
      });
    }
  }

  #getUnits(responseData) {
    if (Array.isArray(responseData?.sparse_board?.units)) {
      return responseData.sparse_board.units;
    }
    if (Array.isArray(responseData?.game?.board?.units)) {
      return responseData.game.board.units;
    }
    if (Array.isArray(responseData?.units)) {
      return responseData.units;
    }
    return null;
  }

  #getDefensiveFireEvents(responseData) {
    return Array.isArray(responseData?.defensive_fire_events)
      ? responseData.defensive_fire_events
      : [];
  }
}
