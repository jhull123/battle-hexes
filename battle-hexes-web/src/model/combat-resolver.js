import { API_URL } from './battle-api';
import axios from 'axios';
import { BoardUpdater } from './board-updater';

export class CombatResolver {
  #gameId;
  #board;

  constructor(gameId, board) {
    this.#gameId = gameId;
    this.#board = board;
  }

  async resolveCombat() {
    const sparseBoard = this.#board.sparseBoard();
    console.log(`${this.#gameId} - ${sparseBoard}`);

    const combatResult = await axios.post(
      `${API_URL}/games/${this.#gameId}/combat`, 
      sparseBoard);
    console.log('combat result: ', combatResult.data.last_combat_results);
    console.log('new board state: ', combatResult.data.units);

    const boardUpdater = new BoardUpdater();
    boardUpdater.updateBoard(this.#board, combatResult.data.units);
    return combatResult.data;
  }
}
