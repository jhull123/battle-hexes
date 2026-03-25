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
import { BoardUpdater } from '../../src/model/board-updater.js';
import { eventBus } from '../../src/event-bus.js';

const mockUpdateBoard = jest.fn();
jest.mock('../../src/model/board-updater.js', () => ({
  BoardUpdater: jest.fn().mockImplementation(() => ({
    updateBoard: mockUpdateBoard,
  })),
}));
jest.mock('../../src/event-bus.js', () => ({
  eventBus: {
    emit: jest.fn(),
  },
}));

const mockService = {
  generateCpuMovement: jest.fn(),
  endMovement: jest.fn(),
  endTurn: jest.fn(),
};

describe('CpuPlayer', () => {
  let cpuPlayer;
  let game;

  beforeEach(() => {
    mockService.generateCpuMovement.mockReset();
    mockService.endMovement.mockReset();
    mockService.endTurn.mockReset();
    mockService.generateCpuMovement.mockResolvedValue({ game: { board: { units: [] } }, plans: [] });
    mockService.endMovement.mockResolvedValue({});
    mockService.endTurn.mockResolvedValue({});
    mockUpdateBoard.mockClear();
    MovementAnimator.mockClear();
    eventBus.emit.mockClear();
    cpuPlayer = new CpuPlayer('CPU', undefined, { service: mockService });
    const board = new Board(1, 1);
    const players = new Players([cpuPlayer, new Player('Dummy')]);
    game = new Game('game-1', ['Movement', 'Combat', 'End Turn'], players, board);
    jest.spyOn(game, 'isGameOver').mockReturnValue(false);
  });
  afterEach(() => {
    jest.useRealTimers();
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
    expect(mockService.generateCpuMovement).toHaveBeenCalledWith(game.getId());
    expect(mockService.endMovement).toHaveBeenCalledWith(
      game.getId(),
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
    expect(mockService.endTurn).toHaveBeenCalledWith(
      game.getId(),
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
    expect(mockService.generateCpuMovement).toHaveBeenCalledWith(game.getId());
    expect(mockService.endMovement).toHaveBeenCalledWith(
      game.getId(),
      game.getBoard().sparseBoard()
    );
    expect(mockService.generateCpuMovement).toHaveBeenCalledTimes(1);
    expect(mockService.endMovement).toHaveBeenCalledTimes(1);

    // End Turn phase: after 2s, axios.post for end-turn
    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();
    expect(mockService.endTurn).toHaveBeenCalledWith(
      game.getId(),
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
    expect(mockService.endTurn).toHaveBeenCalledWith(
      game.getId(),
      game.getBoard().sparseBoard()
    );
    await playPromise;
  });



  test('does not wipe scores when end-turn request fails', async () => {
    jest.useFakeTimers();

    const board = new Board(1, 1);
    const players = new Players([cpuPlayer, new Player('Dummy')]);
    game = new Game('game-1', ['End Turn'], players, board);
    jest.spyOn(game, 'isGameOver').mockReturnValue(false);

    const updateScoresSpy = jest.spyOn(game, 'updateScores');
    const updateTurnStateSpy = jest.spyOn(game, 'updateTurnState');

    mockService.endTurn.mockRejectedValueOnce(new Error('network down'));

    const playPromise = cpuPlayer.play(game);
    await jest.runOnlyPendingTimersAsync();
    await playPromise;

    expect(mockService.endTurn).toHaveBeenCalledWith(
      game.getId(),
      game.getBoard().sparseBoard()
    );
    expect(updateScoresSpy).not.toHaveBeenCalled();
    expect(updateTurnStateSpy).not.toHaveBeenCalled();
  });

  test('animates movement plans returned from server', async () => {
    jest.useFakeTimers();
    const board = new Board(1, 2);
    const players = new Players([cpuPlayer, new Player('Dummy')]);
    game = new Game('g2', ['Movement', 'End Turn'], players, board);
    jest.spyOn(game, 'isGameOver').mockReturnValue(false);
    const unit = new Unit('unit-001');
    board.addUnit(unit, 0, 0);
    mockService.generateCpuMovement.mockResolvedValueOnce({
      game: { board: { units: [] } },
      plans: [
        {
          unit_id: 'unit-001',
          path: [ { row: 0, column: 0 }, { row: 0, column: 1 } ],
        },
      ],
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

    expect(mockService.generateCpuMovement).not.toHaveBeenCalled();
    expect(mockService.endMovement).not.toHaveBeenCalled();
    expect(mockService.endTurn).not.toHaveBeenCalled();
  });

  test('emits redraw after ending turn so defensive fire icons refresh for the next player', async () => {
    jest.useFakeTimers();
    const board = new Board(1, 1);
    const players = new Players([cpuPlayer, new Player('Dummy')]);
    game = new Game('game-1', ['End Turn'], players, board);
    jest.spyOn(game, 'isGameOver').mockReturnValue(false);

    const playPromise = cpuPlayer.play(game);
    await jest.runOnlyPendingTimersAsync();
    await playPromise;

    expect(eventBus.emit).toHaveBeenCalledWith('redraw');
    expect(eventBus.emit).toHaveBeenCalledWith('menuUpdate');
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

    expect(mockService.generateCpuMovement).toHaveBeenCalledWith(game.getId());
    expect(mockService.endMovement).toHaveBeenCalledWith(
      game.getId(),
      game.getBoard().sparseBoard()
    );

    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();

    await playPromise;

    expect(mockService.generateCpuMovement).toHaveBeenCalledTimes(1);
    expect(mockService.endMovement).toHaveBeenCalledTimes(1);
  });
});
