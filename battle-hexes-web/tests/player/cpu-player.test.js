import axios from 'axios';
import { MovementAnimator } from '../../src/animation/movement-animator.js';
jest.mock('../../src/animation/movement-animator.js', () => ({
  MovementAnimator: jest.fn().mockImplementation(() => ({
    animate: jest.fn().mockResolvedValue(),
  })),
}));
import { CpuPlayer } from '../../src/player/cpu-player.js';
import { Game } from '../../src/model/game.js';
import { Board } from '../../src/model/board.js';
import { Unit } from '../../src/model/unit.js';
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
    MovementAnimator.mockClear();
    cpuPlayer = new CpuPlayer('CPU');
    const board = new Board(1, 1);
    const players = new Players([cpuPlayer, new Player('Dummy')]);
    game = new Game('game-1', ['Movement', 'Combat', 'End Turn'], players, board);
    jest.spyOn(game, 'isGameOver').mockReturnValue(false);
  });

  test('calls movement endpoint during movement phase and advances phase based on combat', async () => {
    jest.useFakeTimers();
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(true);
    const resolveCombatSpy = jest.spyOn(game, 'resolveCombat').mockResolvedValue();

    const playPromise = cpuPlayer.play(game);
    await Promise.resolve();

    // Movement phase: after 2s, axios.post for movement
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(axios.post).toHaveBeenCalledWith(`${API_URL}/games/${game.getId()}/movement`);
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/end-movement`,
      game.getBoard().sparseBoard()
    );
    expect(mockUpdateBoard).toHaveBeenCalledWith(game.getBoard(), []);

    // Combat phase: after 2s, resolveCombat
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(resolveCombatSpy).toHaveBeenCalled();

    // End Turn phase: after 2s, axios.post for end-turn
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/end-turn`,
      game.getBoard().sparseBoard()
    );

    // After all phases, phase should be back to Movement
    await playPromise;
    expect(game.getCurrentPhase()).toBe('Movement');
  });

  test('skips combat when there is none and automatically ends turn', async () => {
    jest.useFakeTimers();
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(false);

    const playPromise = cpuPlayer.play(game);
    await Promise.resolve();

    // Movement phase: after 2s, axios.post for movement
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/movement`
    );
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/end-movement`,
      game.getBoard().sparseBoard()
    );
    expect(axios.post).toHaveBeenCalledTimes(2);

    // End Turn phase: after 2s, axios.post for end-turn
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/end-turn`,
      game.getBoard().sparseBoard()
    );
    await playPromise;
    // After all phases, phase should be back to Movement
    expect(game.getCurrentPhase()).toBe('Movement');
  });

  test('resolves combat when starting in combat phase', async () => {
    jest.useFakeTimers();
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(true);
    game.endPhase(); // move to Combat phase
    const resolveCombatSpy = jest.spyOn(game, 'resolveCombat').mockResolvedValue();

    const playPromise = cpuPlayer.play(game);
    await Promise.resolve();

    // Combat phase: after 2s, resolveCombat
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(resolveCombatSpy).toHaveBeenCalled();

    // End Turn phase: after 2s, axios.post for end-turn
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/end-turn`,
      game.getBoard().sparseBoard()
    );
    await playPromise;
  });

  test('animates movement plans returned from server', async () => {
    jest.useFakeTimers();
    const board = new Board(1, 2);
    const players = new Players([cpuPlayer, new Player('Dummy')]);
    game = new Game('g2', ['Movement', 'End Turn'], players, board);
    jest.spyOn(game, 'isGameOver').mockReturnValue(false);
    const unit = new Unit('unit-001');
    board.addUnit(unit, 0, 0);
    axios.post.mockResolvedValueOnce({
      data: {
        game: { board: { units: [] } },
        plans: [
          {
            unit_id: 'unit-001',
            path: [ { row: 0, column: 0 }, { row: 0, column: 1 } ]
          }
        ]
      }
    });

    const playPromise = cpuPlayer.play(game);
    await Promise.resolve();

    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();

    expect(MovementAnimator).toHaveBeenCalledWith(game.getBoard());
    expect(MovementAnimator.mock.calls.length).toBeGreaterThan(1);
    expect(mockUpdateBoard).toHaveBeenCalled();

    await jest.runOnlyPendingTimersAsync();
    await playPromise;
  });

  test('does not take action when game is already over', async () => {
    jest.spyOn(game, 'isGameOver').mockReturnValue(true);

    await cpuPlayer.play(game);

    expect(axios.post).not.toHaveBeenCalled();
  });

  test('stops playing when game becomes over mid-turn', async () => {
    jest.useFakeTimers();
    const isGameOverSpy = jest.spyOn(game, 'isGameOver');
    isGameOverSpy.mockReturnValueOnce(false).mockReturnValue(true);
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(false);

    const playPromise = cpuPlayer.play(game);
    await Promise.resolve();

    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();

    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/movement`
    );
    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/${game.getId()}/end-movement`,
      game.getBoard().sparseBoard()
    );

    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();

    await playPromise;

    expect(axios.post).toHaveBeenCalledTimes(2);
  });
});
