import { eventBus } from '../event-bus.js';
import { BoardUpdater } from './board-updater.js';

export function applyMovementResponse(board, response) {
  const units = response?.game?.board?.units ?? response?.sparse_board?.units ?? [];
  new BoardUpdater().updateBoard(board, units);

  const defensiveFireEvents = response?.defensive_fire_events ?? [];
  if (defensiveFireEvents.length > 0) {
    eventBus.emit('defensiveFireResolved', defensiveFireEvents);
  }
}
