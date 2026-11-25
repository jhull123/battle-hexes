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
      { id: 'random', name: 'Random Player' },
      { id: 'q-learning', name: 'Q-Learning Player' },
      { id: 'scripted', name: 'Scripted Player' },
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
    const first = document.getElementById('player1-type');
    const second = document.getElementById('player2-type');
    expect([first.value, second.value]).toEqual(['human', 'q-learning']);
    first.value = 'scripted';
    second.value = 'scripted';

    document.getElementById('enter-battle-button').click();
    await flushPromises();

    expect(mockService.createGame).toHaveBeenCalledWith({
      scenarioId: 'elim_1',
      playerTypes: ['scripted', 'scripted'],
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

  test('keeps the scripted opponent selected when switching scenarios', async () => {
    mockService.listScenarios.mockResolvedValue([
      { id: 'elim_1', name: 'Scenario 1' },
      { id: 'elim_2', name: 'Scenario 2' },
      { id: 'ppo_9x9_experimental', name: 'Elimination Demo 3' },
    ]);
    mockService.listPlayerTypes.mockResolvedValue([
      { id: 'human', name: 'Human' },
      { id: 'random', name: 'Random Player' },
      { id: 'q-learning', name: 'Q-Learning Player' },
      { id: 'scripted', name: 'Scripted Player' },
      { id: 'ppo-9x9-experimental', name: 'Trained 9×9 PPO' },
    ]);
    await import('../../src/title-screen.js');
    await flushPromises();
    const scenario = document.getElementById('scenario-select');
    const first = document.getElementById('player1-type');
    const second = document.getElementById('player2-type');
    const ordinaryTypes = ['human', 'random', 'q-learning', 'scripted'];
    const selectScenario = (id) => {
      scenario.value = id;
      scenario.dispatchEvent(new Event('change'));
    };

    first.value = 'scripted';
    second.value = 'scripted';
    selectScenario('elim_2');
    expect([first.value, second.value]).toEqual(['scripted', 'scripted']);
    selectScenario('ppo_9x9_experimental');
    expect([...first.options].map((option) => option.value)).toEqual(['ppo-9x9-experimental']);
    expect([...second.options].map((option) => option.value)).toEqual(ordinaryTypes);
    expect([first.value, second.value]).toEqual(['ppo-9x9-experimental', 'scripted']);
    selectScenario('elim_1');
    expect([...first.options].map((option) => option.value)).toEqual(ordinaryTypes);
    expect(second.value).toBe('scripted');
  });
});
