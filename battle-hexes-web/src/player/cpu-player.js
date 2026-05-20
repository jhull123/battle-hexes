import { playerTypes, Player } from './player.js';
import { battleHexesService } from '../service/service-factory.js';
import { eventBus } from '../event-bus.js';
import { MovementAnimator } from '../animation/movement-animator.js';
import { applyMovementResponse } from '../model/movement-response-handler.js';

export class CpuPlayer extends Player {
  static PHASE_DELAY_MS = 333;

  constructor(name, factions, { service = battleHexesService } = {}) {
    super(name, playerTypes.CPU, factions);
    this.service = service;
  }

  async play(game) {
    if (game.isGameOver()) {
      return;
    }
    console.log(`Playing phase: ${game.getCurrentPhase()}`);
    
    if (game.getCurrentPhase() === 'Movement') {
      try {
        await new Promise(resolve => setTimeout(resolve, CpuPlayer.PHASE_DELAY_MS));
        const responseData = await this.service.generateCpuMovement(game.getId());
        console.log('CPU movement plans:', responseData);

        const animator = new MovementAnimator(game.getBoard());
        for (const plan of responseData.plans) {
          const unit = [...game.getBoard().units].find(
            u => u.getId() === plan.unit_id
          );
          if (unit) {
            const path = plan.path.map(h =>
              game.getBoard().getHex(h.row, h.column)
            );
            await animator.animate(unit, path);
          }
        }

        applyMovementResponse(game.getBoard(), responseData);

        await this.service.endMovement(
          game.getId(),
          game.getBoard().sparseBoard()
        );

        game.endPhase();
        eventBus.emit('redraw');
        eventBus.emit('menuUpdate');

        return this.play(game);
      } catch (err) {
        console.error('Failed to fetch CPU movement plans', err);
      }
    } else if (game.getCurrentPhase() === 'Combat') {
      try {
        await new Promise(resolve => setTimeout(resolve, CpuPlayer.PHASE_DELAY_MS));
        await game.resolveCombat();
        game.endPhase();
        eventBus.emit('redraw');
        eventBus.emit('menuUpdate');

        return this.play(game);
      } catch (err) {
        console.error('Failed to resolve combat', err);
      }
    } else if (game.getCurrentPhase() === 'End Turn') {
      await new Promise(resolve => setTimeout(resolve, CpuPlayer.PHASE_DELAY_MS));
      const endTurnResponse = await this.service.endTurn(
        game.getId(),
        game.getBoard().sparseBoard()
      ).catch(err => {
        console.error('Failed to update game state', err);
        return null;
      });
      if (endTurnResponse) {
        game.updateScores?.(endTurnResponse.scores);
        game.updateTurnState?.({
          turnLimit: endTurnResponse.turnLimit,
          turnNumber: endTurnResponse.turnNumber,
        });
      }
      game.endPhase();
      eventBus.emit('redraw');
      eventBus.emit('menuUpdate');
      if (!game.isGameOver()) {
        game.getCurrentPlayer().play(game);
      }
    }

    console.log(`${this.getName()} is playing ${game.getId()}.`);
  }
}
