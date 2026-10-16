import { CpuPlayer } from './cpu-player.js';
import { MovementAnimator } from '../animation/movement-animator.js';
import { applyMovementResponse } from '../model/movement-response-handler.js';
import { eventBus } from '../event-bus.js';

/** A single server-side prediction and its fire must finish before the next. */
export class PpoPlayer extends CpuPlayer {
  async play(game) {
    while (!game.isGameOver() && game.getCurrentPlayer() === this
           && game.getCurrentPhase() === 'Movement'
           && game.ppoTurn.pendingUnitIds.length > 0) {
      try {
        const response = await this.service.orderPpo(game.getId());
        const unit = game.getUnitById(response.plan.unitId);
        if (unit) {
          const path = response.plan.path.map(({ row, column }) =>
            game.getBoard().getHex(row, column));
          await new MovementAnimator(game.getBoard()).animate(unit, path);
        }
        applyMovementResponse(game.getBoard(), response);
        game.applyApiState(response);
        this.service.acknowledgeResponseApplication(game.getId());
        eventBus.emit('menuUpdate');
        eventBus.emit('redraw');
      } catch (error) {
        console.error('Experimental PPO order failed', error);
        return;
      }
    }
    const nextPlayer = game.getCurrentPlayer();
    if (!game.isGameOver() && nextPlayer && nextPlayer !== this
        && !nextPlayer.isHuman()) {
      return nextPlayer.play(game);
    }
  }
}
