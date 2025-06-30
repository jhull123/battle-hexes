import { playerTypes, Player } from './player.js';
import axios from 'axios';
import { API_URL } from '../model/battle-api.js';

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
      } catch (err) {
        console.error('Failed to fetch CPU movement plans', err);
      }
    }

    console.log(`${this.getName()} is playing ${game.getId()}.`);
  }
}