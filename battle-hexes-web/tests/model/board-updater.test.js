import { Board } from '../../src/model/board.js';
import { BoardUpdater } from '../../src/model/board-updater.js';
import { Faction } from '../../src/model/faction.js';

describe('updateBoard', () => {
  let board, boardUpdater;

  beforeEach(() => {
    board = new Board(10, 10, [new Faction(), new Faction()]);
    boardUpdater = new BoardUpdater();
  });

  test('update empty board with no units', () => {
    boardUpdater.updateBoard(board, []);
  });
});