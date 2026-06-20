import { eventBus } from '../event-bus.js';
import { BoardUpdater } from './board-updater.js';

export function applyMovementResponse(board, response) {
  const units = response?.game?.board?.units ?? response?.sparseBoard?.units ?? [];
  new BoardUpdater().updateBoard(board, units);

  const defensiveFireEvents = response?.defensiveFireEvents ?? [];
  if (defensiveFireEvents.length > 0) {
    eventBus.emit('defensiveFireResolved', defensiveFireEvents);
  }
}
