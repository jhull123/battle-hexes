/**
 * @jest-environment jsdom
 */

import { jest } from '@jest/globals';

jest.mock('p5', () => jest.fn());

const mockService = {
  listScenarios: jest.fn(),
  listPlayerTypes: jest.fn(),
  createGame: jest.fn(),
};

jest.mock('../../src/service/service-factory.js', () => ({
  battleHexesService: mockService,
}));

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

    mockService.listScenarios.mockResolvedValue([{ id: 'elim_1', name: 'Scenario 1' }]);
    mockService.listPlayerTypes.mockResolvedValue([
      { id: 'human', name: 'Human' },
      { id: 'random', name: 'Random' },
    ]);
  });

  afterEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    delete window.location;
    window.location = originalLocation;
  });

  test('creates a game and redirects to battle page', async () => {
    mockService.createGame.mockResolvedValue({ id: 'game-123' });
    delete window.location;
    window.location = {
      assign: jest.fn(),
      pathname: '/',
      search: '',
    };

    await import('../../src/title-screen.js');
    await flushPromises();

    document.getElementById('scenario-select').value = 'elim_1';
    document.getElementById('player1-type').value = 'human';
    document.getElementById('player2-type').value = 'random';

    document.getElementById('enter-battle-button').click();
    await flushPromises();

    expect(mockService.createGame).toHaveBeenCalledWith({
      scenarioId: 'elim_1',
      playerTypes: ['human', 'random'],
    });
    expect(window.location.assign).toHaveBeenCalledWith('battle.html?gameId=game-123');
  });

  test('shows error message when game creation fails', async () => {
    mockService.createGame.mockRejectedValue(new Error('failed'));
    delete window.location;
    window.location = {
      assign: jest.fn(),
      pathname: '/',
      search: '',
    };

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

  test('experimental scenario restricts both seats and restores ordinary choices', async () => {
    mockService.listScenarios.mockResolvedValue([
      { id: 'elim_1', name: 'Scenario 1' },
      { id: 'ppo_9x9_experimental', name: 'Experimental — trained 9×9 PPO (no skill claim)' },
    ]);
    mockService.listPlayerTypes.mockResolvedValue([
      { id: 'human', name: 'Human' },
      { id: 'random', name: 'Random' },
      { id: 'ppo-9x9-experimental', name: 'Experimental — trained 9×9 PPO (no skill claim)' },
    ]);
    await import('../../src/title-screen.js');
    await flushPromises();
    const scenario = document.getElementById('scenario-select');
    scenario.value = 'ppo_9x9_experimental';
    scenario.dispatchEvent(new Event('change'));
    const first = document.getElementById('player1-type');
    const second = document.getElementById('player2-type');
    expect([...first.options].map((option) => option.value)).toEqual(['ppo-9x9-experimental']);
    expect([...second.options].map((option) => option.value)).toEqual(['human']);
    scenario.value = 'elim_1';
    scenario.dispatchEvent(new Event('change'));
    expect([...first.options].map((option) => option.value)).toEqual(['human', 'random']);
  });
});
