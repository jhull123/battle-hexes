/**
 * @jest-environment jsdom
 */

import {
  DEFAULT_STATUS_MESSAGE,
  EMPTY_MESSAGE,
  LOADING_MESSAGE,
  UNAVAILABLE_MESSAGE,
  loadScenarios,
  populateScenarioOptions,
} from '../../src/title-screen-scenarios.js';

describe('title screen scenario helpers', () => {
  let selectElement;
  let statusElement;

  beforeEach(() => {
    selectElement = document.createElement('select');
    statusElement = document.createElement('p');
  });

  test('populateScenarioOptions fills select and selects first entry', () => {
    populateScenarioOptions(selectElement, [
      { id: 'alpha', name: 'Alpha Strike' },
      { id: 'beta' },
    ]);

    expect(selectElement.options).toHaveLength(2);
    expect(selectElement.options[0].value).toBe('alpha');
    expect(selectElement.options[0].selected).toBe(true);
    expect(selectElement.options[1].textContent).toBe('beta');
  });

  test('loadScenarios populates select with fetched scenarios', async () => {
    const scenarios = [
      { id: 'alpha', name: 'Alpha Strike' },
      { id: 'beta', name: 'Beta Shield' },
    ];
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => scenarios,
    });

    const loadPromise = loadScenarios({
      selectElement,
      statusElement,
      fetchImpl,
      apiUrl: 'https://api.example.com',
    });

    expect(statusElement.textContent).toBe(LOADING_MESSAGE);

    const result = await loadPromise;

    expect(result).toEqual(scenarios);
    expect(selectElement.disabled).toBe(false);
    expect(selectElement.value).toBe('alpha');
    expect(statusElement.textContent).toBe(DEFAULT_STATUS_MESSAGE);
  });

  test('loadScenarios handles empty response', async () => {
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    const result = await loadScenarios({
      selectElement,
      statusElement,
      fetchImpl,
      apiUrl: 'https://api.example.com',
    });

    expect(result).toEqual([]);
    expect(selectElement.disabled).toBe(true);
    expect(selectElement.innerHTML).toContain('No scenarios available');
    expect(statusElement.textContent).toBe(EMPTY_MESSAGE);
  });

  test('loadScenarios handles failed request', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    const result = await loadScenarios({
      selectElement,
      statusElement,
      fetchImpl,
      apiUrl: 'https://api.example.com',
    });

    expect(result).toEqual([]);
    expect(selectElement.innerHTML).toContain('Unable to load scenarios');
    expect(selectElement.disabled).toBe(true);
    expect(statusElement.textContent).toBe(UNAVAILABLE_MESSAGE);
    consoleSpy.mockRestore();
  });
});
