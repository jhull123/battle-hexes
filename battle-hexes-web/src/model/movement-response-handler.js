import { eventBus } from '../event-bus.js';
import { BoardUpdater } from './board-updater.js';

const REASON_TO_MESSAGE = {
  STACKING_LIMIT_EXCEEDED: 'Destination hex is full due to the scenario stacking limit.',
};

function getPlanReasonCode(plan) {
  if (!plan || typeof plan !== 'object') {
    return null;
  }
  return plan.reason_code ?? plan.reason ?? plan.invalid_reason ?? plan.failure_reason ?? null;
}

function getPlanDestinationHex(plan, board) {
  const path = Array.isArray(plan?.path) ? plan.path : [];
  if (path.length === 0) {
    return null;
  }
  const destination = path[path.length - 1];
  if (!destination) {
    return null;
  }
  return board.getHex?.(destination.row, destination.column) ?? null;
}

export function applyMovementResponse(board, response) {
  const boardUpdater = new BoardUpdater();
  const units = response?.game?.board?.units ?? response?.sparse_board?.units ?? [];
  boardUpdater.clearMoveHoverIllegalReasons(board);
  boardUpdater.updateBoard(board, units);

  const defensiveFireEvents = response?.defensive_fire_events ?? [];
  if (defensiveFireEvents.length > 0) {
    eventBus.emit('defensiveFireResolved', defensiveFireEvents);
  }

  const rejectedPlans = (response?.plans ?? [])
    .map((plan) => {
      const reasonCode = getPlanReasonCode(plan);
      return { plan, reasonCode };
    })
    .filter(({ reasonCode }) => reasonCode !== null);

  for (const { plan, reasonCode } of rejectedPlans) {
    const destinationHex = getPlanDestinationHex(plan, board);
    destinationHex?.setMoveHoverIllegalReason(reasonCode);

    if (REASON_TO_MESSAGE[reasonCode]) {
      eventBus.emit('movementRejected', {
        reasonCode,
        message: REASON_TO_MESSAGE[reasonCode],
        plan,
      });
    }
  }
}
