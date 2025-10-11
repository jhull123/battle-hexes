/** @jest-environment jsdom */

jest.mock('../../src/model/game.js', () => ({
  Game: {
    fetchGameFromServer: jest.fn(),
    newGameFromServer: jest.fn(),
  },
}));

import { Game } from '../../src/model/game.js';
import {
  extractGameIdFromLocation,
  getLastLoadedConfig,
  loadGameData,
  rememberLoadedGameData,
  updateUrlWithGameId,
} from '../../src/model/game-loader.js';

const flushPromises = () => new Promise((resolve) => process.nextTick(resolve));

describe('game loader helpers', () => {
  beforeEach(() => {
    Game.fetchGameFromServer.mockReset();
    Game.newGameFromServer.mockReset();
    history.replaceState(null, '', '/battle.html');
    rememberLoadedGameData({
      scenarioId: 'elem_1',
      playerTypeIds: ['human', 'random'],
    });
  });

  test('extracts game id from battle path', () => {
    history.replaceState(null, '', '/battle.html/existing-game');
    expect(extractGameIdFromLocation()).toBe('existing-game');
  });

  test('extracts game id from query string', () => {
    history.replaceState(null, '', '/battle.html?gameId=query-game');
    expect(extractGameIdFromLocation()).toBe('query-game');
  });

  test('updateUrlWithGameId replaces path segment and query string', () => {
    history.replaceState(null, '', '/battle.html/old-game?foo=bar');
    const replaceSpy = jest.spyOn(history, 'replaceState').mockImplementation(() => {});

    updateUrlWithGameId('new-game');

    expect(replaceSpy).toHaveBeenCalled();
    const urlArg = replaceSpy.mock.calls[0][2];
    const updatedUrl = new URL(`http://localhost${urlArg}`);
    expect(updatedUrl.pathname).toBe('/battle.html/new-game');
    expect(updatedUrl.searchParams.get('foo')).toBe('bar');
    expect(updatedUrl.searchParams.get('gameId')).toBe('new-game');

    replaceSpy.mockRestore();
  });

  test('loadGameData fetches existing game and updates url', async () => {
    history.replaceState(null, '', '/battle.html/existing-game');
    Game.fetchGameFromServer.mockResolvedValue({
      id: 'fetched-game',
      playerTypeIds: ['human', 'q-learning'],
    });
    const replaceSpy = jest.spyOn(history, 'replaceState').mockImplementation(() => {});

    const gameData = await loadGameData();
    await flushPromises();

    expect(Game.fetchGameFromServer).toHaveBeenCalledWith('existing-game');
    expect(Game.newGameFromServer).not.toHaveBeenCalled();
    expect(gameData).toEqual({
      id: 'fetched-game',
      playerTypeIds: ['human', 'q-learning'],
    });

    const urlArg = replaceSpy.mock.calls[0][2];
    const updatedUrl = new URL(`http://localhost${urlArg}`);
    expect(updatedUrl.pathname).toBe('/battle.html/fetched-game');
    expect(updatedUrl.searchParams.get('gameId')).toBe('fetched-game');
    expect(getLastLoadedConfig()).toEqual({
      scenarioId: 'elem_1',
      playerTypes: ['human', 'q-learning'],
    });

    replaceSpy.mockRestore();
  });

  test('loadGameData creates new game when none provided', async () => {
    history.replaceState(null, '', '/battle.html');
    Game.newGameFromServer.mockResolvedValue({
      id: 'new-game',
      playerTypeIds: ['random', 'q-learning'],
    });
    const replaceSpy = jest.spyOn(history, 'replaceState').mockImplementation(() => {});

    const gameData = await loadGameData();
    await flushPromises();

    expect(Game.fetchGameFromServer).not.toHaveBeenCalled();
    expect(Game.newGameFromServer).toHaveBeenCalledTimes(1);
    expect(gameData).toEqual({
      id: 'new-game',
      playerTypeIds: ['random', 'q-learning'],
    });

    const urlArg = replaceSpy.mock.calls[0][2];
    const updatedUrl = new URL(`http://localhost${urlArg}`);
    expect(updatedUrl.pathname).toBe('/battle.html');
    expect(updatedUrl.searchParams.get('gameId')).toBe('new-game');
    expect(getLastLoadedConfig()).toEqual({
      scenarioId: 'elem_1',
      playerTypes: ['random', 'q-learning'],
    });

    replaceSpy.mockRestore();
  });

  test('rememberLoadedGameData prefers explicit playerTypeIds arrays', () => {
    rememberLoadedGameData({
      scenarioId: 'elem_2',
      playerTypeIds: ['human', 'q-learning'],
    });

    expect(getLastLoadedConfig()).toEqual({
      scenarioId: 'elem_2',
      playerTypes: ['human', 'q-learning'],
    });
  });

  test('rememberLoadedGameData derives type ids from players when available', () => {
    rememberLoadedGameData({
      scenarioId: 'elem_3',
      players: [
        { typeId: 'human' },
        { metadata: { typeId: 'random' } },
      ],
    });

    expect(getLastLoadedConfig()).toEqual({
      scenarioId: 'elem_3',
      playerTypes: ['human', 'random'],
    });
  });

  test('getLastLoadedConfig returns a clone to avoid accidental mutation', () => {
    const config = getLastLoadedConfig();
    config.playerTypes.push('extra');

    expect(getLastLoadedConfig()).toEqual({
      scenarioId: 'elem_1',
      playerTypes: ['human', 'random'],
    });
  });
});
