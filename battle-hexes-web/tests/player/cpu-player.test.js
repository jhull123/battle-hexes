import axios from 'axios';
import { CpuPlayer } from '../../src/player/cpu-player.js';
import { Game } from '../../src/model/game.js';
import { Board } from '../../src/model/board.js';
import { Player, Players } from '../../src/player/player.js';
import { API_URL } from '../../src/model/battle-api.js';
import { BoardUpdater } from '../../src/model/board-updater.js';

jest.mock('axios');
const mockUpdateBoard = jest.fn();
jest.mock('../../src/model/board-updater.js', () => ({
  BoardUpdater: jest.fn().mockImplementation(() => ({
    updateBoard: mockUpdateBoard,
  })),
}));

describe('CpuPlayer', () => {
  let cpuPlayer;
  let game;

  beforeEach(() => {
    axios.post.mockClear();
    axios.post.mockResolvedValue({ data: { game: { board: { units: [] } }, plans: [] } });
    mockUpdateBoard.mockClear();
    cpuPlayer = new CpuPlayer('CPU');
    const board = new Board(1, 1);
    const players = new Players([cpuPlayer, new Player('Dummy')]);
    game = new Game('game-1', ['Movement', 'Combat', 'End Turn'], players, board);
  });

  test('calls movement endpoint during movement phase and advances phase based on combat', async () => {
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(true);
    await cpuPlayer.play(game);
    expect(axios.post).toHaveBeenCalledWith(`${API_URL}/games/${game.getId()}/movement`);
    expect(mockUpdateBoard).toHaveBeenCalledWith(game.getBoard(), []);
    expect(game.getCurrentPhase()).toBe('Combat');
  });

  test('skips combat when there is none and automatically ends turn', async () => {
    jest.useFakeTimers();
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(false);

    const playPromise = cpuPlayer.play(game);
    await Promise.resolve();

    expect(game.getCurrentPhase()).toBe('End Turn');
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/movement`
    );
    expect(axios.post).toHaveBeenCalledTimes(1);

    await jest.runAllTimersAsync();
    await playPromise;

    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/end-turn`,
      game.getBoard().sparseBoard()
    );
    expect(game.getCurrentPhase()).toBe('Movement');
  });

  test('does not call endpoint in other phases', async () => {
    game.endPhase(); // move to Combat phase
    await cpuPlayer.play(game);
    expect(axios.post).not.toHaveBeenCalled();
    expect(mockUpdateBoard).not.toHaveBeenCalled();
  });
});
