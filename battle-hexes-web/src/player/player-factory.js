import { playerTypes, Player } from './player.js';
import { CpuPlayer } from './cpu-player.js';

export class PlayerFactory {
  createPlayer(name, type, factions) {
    switch (type) {
      case playerTypes.HUMAN:
        return new Player(name, type, factions);
      case playerTypes.CPU:
        return new CpuPlayer(name, factions);
      default:
        throw new Error(`Unknown player type: ${type}`);
    }
  }
}