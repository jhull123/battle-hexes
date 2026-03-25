import { BoardUpdater } from './board-updater';
import { battleHexesService } from '../service/service-factory.js';

export class CombatResolver {
  #gameId;
  #board;

  constructor(gameId, board, { service = battleHexesService } = {}) {
    this.#gameId = gameId;
    this.#board = board;
    this.service = service;
  }

  async resolveCombat() {
    const sparseBoard = this.#board.sparseBoard();
    console.log(`${this.#gameId} - ${sparseBoard}`);

    const combatResult = await this.service.resolveCombat(this.#gameId, sparseBoard);
    console.log('combat result: ', combatResult.last_combat_results);
    console.log('new board state: ', combatResult.units);

    const boardUpdater = new BoardUpdater();
    boardUpdater.updateBoard(this.#board, combatResult.units);
    return combatResult;
  }
}
