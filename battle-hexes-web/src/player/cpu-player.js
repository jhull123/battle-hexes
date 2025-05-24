import { playerTypes, Player } from './player.js';

export class CpuPlayer extends Player {
  constructor(name, factions) {
    super(name, playerTypes.CPU, factions);
  }

  async play(game) {
    // TODO Implement CPU logic to make a move based on the game state
    console.log(`${this.getName()} is playing ${game.getId()}.`);
  }
}