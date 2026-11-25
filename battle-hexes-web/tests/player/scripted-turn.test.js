/**
 * @jest-environment jsdom
 */

import { Game } from '../../src/model/game.js';
import { GameCreator } from '../../src/model/game-creator.js';
import { loadGameData } from '../../src/model/game-loader.js';
import { CpuPlayer } from '../../src/player/cpu-player.js';
import { battleHexesService as mockService } from '../../src/service/service-factory.js';

jest.mock('../../src/service/service-factory.js', () => ({
  battleHexesService: {
    createGame: jest.fn(),
    getGame: jest.fn(),
    generateCpuMovement: jest.fn(),
    endMovement: jest.fn(),
    resolveCombat: jest.fn(),
    endTurn: jest.fn(),
    acknowledgeResponseApplication: jest.fn(),
  },
}));

const board = { rows: 2, columns: 2, units: [] };
const scriptedGame = {
  id: 'scripted-game',
  scenarioId: 'elim_1',
  playerTypeIds: ['scripted', 'scripted'],
  players: ['First', 'Second'].map((name) => ({
    name, type: 'Computer', factions: [],
  })),
  activePlayer: 'First',
  currentPhase: 'movement',
  gameVersion: 1,
  gameStatus: { state: 'in_progress' },
  board,
};

const completedState = {
  gameStatus: { state: 'completed' },
  activePlayer: null,
  currentPhase: null,
};

describe('scripted seat through the ordinary web CPU flow', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    history.replaceState(null, '', '/');
  });

  test('a new scripted-versus-scripted game hands off without human input', async () => {
    const secondTurn = { ...scriptedGame, activePlayer: 'Second', gameVersion: 4 };
    mockService.createGame.mockResolvedValue(scriptedGame);
    mockService.generateCpuMovement
      .mockResolvedValueOnce({ plans: [], game: scriptedGame, gameVersion: 2 })
      .mockResolvedValueOnce({ plans: [], game: secondTurn, gameVersion: 5 });
    mockService.endMovement
      .mockResolvedValueOnce({ game: { ...scriptedGame, currentPhase: 'end_turn' }, gameVersion: 3 })
      .mockResolvedValueOnce({ game: { ...secondTurn, currentPhase: 'end_turn' }, gameVersion: 6 });
    mockService.endTurn
      .mockResolvedValueOnce(secondTurn)
      .mockResolvedValueOnce({ ...secondTurn, ...completedState, gameVersion: 7 });

    const payload = await Game.newGameFromServer({
      scenarioId: 'elim_1', playerTypes: ['scripted', 'scripted'],
    });
    const game = new GameCreator().createGame(payload);
    expect(game.getPlayers().getAllPlayers().every((player) => player instanceof CpuPlayer)).toBe(true);
    const firstTurn = game.getCurrentPlayer().play(game);
    await jest.runAllTimersAsync();
    await firstTurn;

    expect(mockService.generateCpuMovement).toHaveBeenCalledTimes(2);
    expect(mockService.endMovement).toHaveBeenCalledTimes(2);
    expect(mockService.resolveCombat).not.toHaveBeenCalled();
    expect(mockService.endTurn).toHaveBeenCalledTimes(2);
    expect(mockService.acknowledgeResponseApplication).toHaveBeenCalledTimes(6);
    expect(game.gameVersion).toBe(7);
    expect(game.isGameOver()).toBe(true);
  });

  test('a reloaded scripted seat plays pending combat and stops at completion', async () => {
    const reloaded = { ...scriptedGame, activePlayer: 'Second', gameVersion: 4 };
    history.replaceState(null, '', '/battle.html?gameId=scripted-game');
    mockService.getGame.mockResolvedValue(reloaded);
    mockService.generateCpuMovement.mockResolvedValue({ plans: [], game: reloaded, gameVersion: 5 });
    mockService.endMovement.mockResolvedValue({
      game: {
        ...reloaded, currentPhase: 'combat',
        pendingCombats: [{ attackerUnitIds: ['second'], defenderUnitIds: ['first'] }],
      },
      gameVersion: 6,
    });
    mockService.resolveCombat.mockResolvedValue({
      ...completedState, units: [], lastCombatResults: [], gameVersion: 7,
    });

    const game = new GameCreator().createGame(await loadGameData());
    expect(mockService.getGame).toHaveBeenCalledWith('scripted-game');
    expect(game.getCurrentPlayer()).toBeInstanceOf(CpuPlayer);
    expect(game.getCurrentPlayer().getName()).toBe('Second');
    const turn = game.getCurrentPlayer().play(game);
    await jest.runAllTimersAsync();
    await turn;

    expect(mockService.generateCpuMovement).toHaveBeenCalledTimes(1);
    expect(mockService.endMovement).toHaveBeenCalledTimes(1);
    expect(mockService.resolveCombat).toHaveBeenCalledTimes(1);
    expect(mockService.endTurn).not.toHaveBeenCalled();
    expect(mockService.acknowledgeResponseApplication).toHaveBeenCalledTimes(3);
    expect(game.gameVersion).toBe(7);
    expect(game.isGameOver()).toBe(true);
  });
});
