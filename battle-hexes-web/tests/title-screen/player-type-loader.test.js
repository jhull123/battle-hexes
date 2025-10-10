/**
 * @jest-environment jsdom
 */

import {
  DEFAULT_STATUS_MESSAGE,
  EMPTY_MESSAGE,
  UNAVAILABLE_MESSAGE,
  initializePlayerTypePicker,
  loadPlayerTypes,
  populatePlayerTypeOptions,
} from '../../src/title-screen-player-types.js';

describe('title screen player type helpers', () => {
  let player1Select;
  let player2Select;
  let statusElement;

  beforeEach(() => {
    player1Select = document.createElement('select');
    player2Select = document.createElement('select');
    statusElement = document.createElement('p');
  });

  test('populatePlayerTypeOptions selects provided default id', () => {
    const types = [
      { id: 'human', name: 'Human' },
      { id: 'random', name: 'Random' },
    ];

    populatePlayerTypeOptions(player1Select, types, 'random');

    expect(player1Select.options).toHaveLength(2);
    expect(player1Select.value).toBe('random');
    expect(player1Select.options[0].selected).toBe(false);
  });

  test('loadPlayerTypes populates both selects and applies defaults', async () => {
    const playerTypes = [
      { id: 'human', name: 'Human' },
      { id: 'random', name: 'Random' },
    ];
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => playerTypes,
    });

    const result = await loadPlayerTypes({
      selectElements: [player1Select, player2Select],
      statusElement,
      fetchImpl,
      apiUrl: 'https://api.example.com',
      defaultSelections: ['human', 'random'],
    });

    expect(result).toEqual(playerTypes);
    expect(player1Select.disabled).toBe(false);
    expect(player2Select.disabled).toBe(false);
    expect(player1Select.value).toBe('human');
    expect(player2Select.value).toBe('random');
    expect(statusElement.textContent).toBe(DEFAULT_STATUS_MESSAGE);
  });

  test('loadPlayerTypes falls back to first option when default missing', async () => {
    const playerTypes = [
      { id: 'human', name: 'Human' },
      { id: 'random', name: 'Random' },
    ];
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => playerTypes,
    });

    await loadPlayerTypes({
      selectElements: [player1Select],
      statusElement,
      fetchImpl,
      apiUrl: 'https://api.example.com',
      defaultSelections: ['q-learning'],
    });

    expect(player1Select.value).toBe('human');
  });

  test('loadPlayerTypes handles empty response', async () => {
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    const result = await loadPlayerTypes({
      selectElements: [player1Select],
      statusElement,
      fetchImpl,
      apiUrl: 'https://api.example.com',
    });

    expect(result).toEqual([]);
    expect(player1Select.disabled).toBe(true);
    expect(player1Select.innerHTML).toContain('No player types available');
    expect(statusElement.textContent).toBe(EMPTY_MESSAGE);
  });

  test('loadPlayerTypes handles failed request', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    const result = await loadPlayerTypes({
      selectElements: [player1Select, player2Select],
      statusElement,
      fetchImpl,
      apiUrl: 'https://api.example.com',
    });

    expect(result).toEqual([]);
    expect(player1Select.disabled).toBe(true);
    expect(player2Select.disabled).toBe(true);
    expect(player1Select.innerHTML).toContain('Unable to load player types');
    expect(statusElement.textContent).toBe(UNAVAILABLE_MESSAGE);
    consoleSpy.mockRestore();
  });

  test('initializePlayerTypePicker wires up DOM when selects exist', () => {
    const documentRef = {
      getElementById: jest.fn((id) => {
        if (id === 'player1-type') {
          return player1Select;
        }

        if (id === 'player2-type') {
          return player2Select;
        }

        if (id === 'player-type-status') {
          return statusElement;
        }

        return null;
      }),
    };

    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    const result = initializePlayerTypePicker({
      documentRef,
      fetchImpl,
      apiUrl: 'https://api.example.com',
    });

    expect(result).not.toBeNull();
    expect(fetchImpl).toHaveBeenCalled();
  });
});
