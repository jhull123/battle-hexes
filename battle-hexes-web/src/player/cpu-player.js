import { playerTypes, Player } from './player.js';
import axios from 'axios';
import { API_URL } from '../model/battle-api.js';
import { BoardUpdater } from '../model/board-updater.js';
import { eventBus } from '../event-bus.js';
import { MovementAnimator } from '../animation/movement-animator.js';

export class CpuPlayer extends Player {
  constructor(name, factions) {
    super(name, playerTypes.CPU, factions);
  }

  async play(game) {
    if (game.isGameOver()) {
      return;
    }
    console.log(`Playing phase: ${game.getCurrentPhase()}`);
    
    if (game.getCurrentPhase() === 'Movement') {
      try {
        await new Promise(resolve => setTimeout(resolve, 2000));
        const response = await axios.post(
          `${API_URL}/games/${game.getId()}/movement`
        );
        console.log('CPU movement plans:', response.data);

        const animator = new MovementAnimator(game.getBoard());
        for (const plan of response.data.plans) {
          const unit = [...game.getBoard().getUnits()].find(
            u => u.getId() === plan.unit_id
          );
          if (unit) {
            const path = plan.path.map(h =>
              game.getBoard().getHex(h.row, h.column)
            );
            await animator.animate(unit, path);
          }
        }

        const boardUpdater = new BoardUpdater();
        boardUpdater.updateBoard(
          game.getBoard(),
          response.data.game.board.units
        );

        game.endPhase();
        eventBus.emit('menuUpdate');

        return this.play(game);
      } catch (err) {
        console.error('Failed to fetch CPU movement plans', err);
      }
    } else if (game.getCurrentPhase() === 'Combat') {
      try {
        await new Promise(resolve => setTimeout(resolve, 2000));
        await game.resolveCombat();
        game.endPhase();
        eventBus.emit('menuUpdate');

        return this.play(game);
      } catch (err) {
        console.error('Failed to resolve combat', err);
      }
    } else if (game.getCurrentPhase() === 'End Turn') {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await axios.post(
        `${API_URL}/games/${game.getId()}/end-turn`,
        game.getBoard().sparseBoard()
      ).catch(err => console.error('Failed to update game state', err));
      game.endPhase();
      eventBus.emit('menuUpdate');
      if (!game.isGameOver()) {
        game.getCurrentPlayer().play(game);
      }
    }

    console.log(`${this.getName()} is playing ${game.getId()}.`);
  }
}
