import { playerTypes, Player } from './player.js';
import axios from 'axios';
import { API_URL } from '../model/battle-api.js';
import { BoardUpdater } from '../model/board-updater.js';
import { eventBus } from '../event-bus.js';

export class CpuPlayer extends Player {
  constructor(name, factions) {
    super(name, playerTypes.CPU, factions);
  }

  async play(game) {
    if (game.getCurrentPhase() === 'Movement') {
      try {
        const response = await axios.post(
          `${API_URL}/games/${game.getId()}/movement`
        );
        console.log('CPU movement plans:', response.data);
        const boardUpdater = new BoardUpdater();
        boardUpdater.updateBoard(
          game.getBoard(),
          response.data.game.board.units
        );

        game.endPhase();
        eventBus.emit('menuUpdate');
      } catch (err) {
        console.error('Failed to fetch CPU movement plans', err);
      }
    }

    console.log(`${this.getName()} is playing ${game.getId()}.`);
  }
}
