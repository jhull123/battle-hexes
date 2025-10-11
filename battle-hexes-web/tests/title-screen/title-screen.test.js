/**
 * @jest-environment jsdom
 */

import { jest } from '@jest/globals';

jest.mock('p5', () => jest.fn());

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));
const originalLocation = window.location;

describe('title screen interactions', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="title-background"></div>
      <main>
        <select id="scenario-select"></select>
        <p id="scenario-status"></p>
        <select id="player1-type"></select>
        <select id="player2-type"></select>
        <p id="player-type-status"></p>
        <button id="enter-battle-button">Enter Battle</button>
      </main>
    `;
  });

  afterEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    delete window.location;
    window.location = originalLocation;
    delete global.fetch;
  });

  test('creates a game and redirects to battle page', async () => {
    const fetchImpl = jest.fn((url) => {
      if (url.endsWith('/scenarios')) {
        return Promise.resolve({
          ok: true,
          json: async () => [{ id: 'elim_1', name: 'Scenario 1' }],
        });
      }
      if (url.endsWith('/player-types')) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            { id: 'human', name: 'Human' },
            { id: 'random', name: 'Random' },
          ],
        });
      }
      if (url.endsWith('/games')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ id: 'game-123' }),
        });
      }
      throw new Error(`Unexpected URL ${url}`);
    });
    delete window.location;
    window.location = {
      assign: jest.fn(),
      pathname: '/',
      search: '',
    };
    global.fetch = fetchImpl;

    await import('../../src/title-screen.js');

    await flushPromises();

    document.getElementById('scenario-select').value = 'elim_1';
    document.getElementById('player1-type').value = 'human';
    document.getElementById('player2-type').value = 'random';

    document.getElementById('enter-battle-button').click();
    await flushPromises();

    const createGameCall = fetchImpl.mock.calls.find(([url]) => url.endsWith('/games'));
    expect(createGameCall).toBeTruthy();
    const [, options] = createGameCall;
    expect(JSON.parse(options.body)).toEqual({
      scenarioId: 'elim_1',
      playerTypes: ['human', 'random'],
    });
    expect(window.location.assign).toHaveBeenCalledWith('battle.html?gameId=game-123');
  });

  test('shows error message when game creation fails', async () => {
    const fetchImpl = jest.fn((url) => {
      if (url.endsWith('/scenarios')) {
        return Promise.resolve({ ok: true, json: async () => [{ id: 'elim_1', name: 'Scenario' }] });
      }
      if (url.endsWith('/player-types')) {
        return Promise.resolve({
          ok: true,
          json: async () => [
            { id: 'human', name: 'Human' },
            { id: 'random', name: 'Random' },
          ],
        });
      }
      if (url.endsWith('/games')) {
        return Promise.resolve({ ok: false, status: 500 });
      }
      throw new Error(`Unexpected URL ${url}`);
    });
    delete window.location;
    window.location = {
      assign: jest.fn(),
      pathname: '/',
      search: '',
    };
    global.fetch = fetchImpl;

    await import('../../src/title-screen.js');

    await flushPromises();

    document.getElementById('scenario-select').value = 'elim_1';
    document.getElementById('player1-type').value = 'human';
    document.getElementById('player2-type').value = 'random';

    const button = document.getElementById('enter-battle-button');
    button.click();
    await flushPromises();

    expect(button.disabled).toBe(false);
    expect(button.textContent).toBe('Enter Battle');
    expect(document.getElementById('player-type-status').textContent)
      .toBe('Failed to start game. Please try again.');
  });
});
