/** @jest-environment jsdom */
import { Menu } from '../../src/menu';
import { eventBus } from '../../src/event-bus.js';

jest.mock('../../src/event-bus.js', () => ({
  eventBus: {
    emit: jest.fn(),
  },
}));

describe('auto new game persistence', () => {
  function buildDom() {
    document.body.innerHTML = `
      <div id="selHexContents"></div>
      <div id="selHexCoord"></div>
      <div id="selHexTerrain"></div>
      <div id="selHexObjectives"></div>
      <div id="unitMovesLeftDiv"></div>
      <button id="newGameBtn"></button>
      <div id="gameOverLabel"></div>
      <input type="checkbox" id="autoNewGame">
      <input type="checkbox" id="showHexCoords">
      <div id="phasesList"></div>
      <button id="endPhaseBtn"></button>
      <div id="currentTurnLabel"></div>
      <div id="victoryPointsList"></div>
    `;
  }

  function fakeGame(overrides = {}) {
    const baseGame = {
      getBoard: () => ({
        getSelectedHex: () => null,
        isOwnHexSelected: () => false,
        hasCombat: () => false,
      }),
      getPhases: () => ['Movement', 'Combat'],
      getCurrentPhase: () => 'Movement',
      getCurrentPlayer: () => ({
        getName: () => 'P1',
        isHuman: () => true,
        play: jest.fn(),
      }),
      getPlayers: () => ({
        getAllPlayers: () => [],
      }),
      getScores: () => ({}),
      isGameOver: () => false,
      getId: () => 'game-id',
    };

    return { ...baseGame, ...overrides };
  }

  beforeEach(() => {
    eventBus.emit.mockClear();
    window.localStorage.clear();
  });

  test('checkbox reflects url parameter', () => {
    buildDom();
    history.replaceState(null, '', '?autoNewGame=1');
    new Menu(fakeGame());
    expect(document.getElementById('autoNewGame').checked).toBe(true);
  });

  test('changing checkbox updates url parameter', () => {
    buildDom();
    history.replaceState(null, '', '/');
    new Menu(fakeGame());
    const chk = document.getElementById('autoNewGame');
    chk.checked = true;
    chk.dispatchEvent(new Event('change'));
    expect(window.location.search).toBe('?autoNewGame=1');
    chk.checked = false;
    chk.dispatchEvent(new Event('change'));
    expect(window.location.search).toBe('');
  });

  test('hex coordinate checkbox defaults to checked, persists, and emits initial state', () => {
    buildDom();
    history.replaceState(null, '', '/');
    const menu = new Menu(fakeGame());
    const coordsCheckbox = document.getElementById('showHexCoords');
    expect(coordsCheckbox.checked).toBe(true);
    expect(eventBus.emit).toHaveBeenCalledWith('hexCoordsVisibilityChanged', true);
    expect(window.localStorage.getItem('battleHexes.showHexCoords')).toBe('true');
    expect(menu.getShowHexCoordsPreference()).toBe(true);
  });

  test('changing hex coordinate checkbox emits visibility changes', () => {
    buildDom();
    history.replaceState(null, '', '/');
    new Menu(fakeGame());
    const coordsCheckbox = document.getElementById('showHexCoords');

    eventBus.emit.mockClear();
    coordsCheckbox.checked = false;
    coordsCheckbox.dispatchEvent(new Event('change'));
    expect(eventBus.emit).toHaveBeenCalledWith('hexCoordsVisibilityChanged', false);
    expect(window.localStorage.getItem('battleHexes.showHexCoords')).toBe('false');

    eventBus.emit.mockClear();
    coordsCheckbox.checked = true;
    coordsCheckbox.dispatchEvent(new Event('change'));
    expect(eventBus.emit).toHaveBeenCalledWith('hexCoordsVisibilityChanged', true);
    expect(window.localStorage.getItem('battleHexes.showHexCoords')).toBe('true');
  });

  test('hex coordinate checkbox restores state from localStorage', () => {
    buildDom();
    window.localStorage.setItem('battleHexes.showHexCoords', 'false');
    const menu = new Menu(fakeGame());

    const coordsCheckbox = document.getElementById('showHexCoords');
    expect(coordsCheckbox.checked).toBe(false);
    expect(eventBus.emit).toHaveBeenCalledWith('hexCoordsVisibilityChanged', false);
    expect(menu.getShowHexCoordsPreference()).toBe(false);
  });

  describe('new game button behaviour', () => {
    const flushPromises = () => new Promise((resolve) => queueMicrotask(resolve));

    test('disables button during request and re-enables afterwards', async () => {
      buildDom();
      history.replaceState(null, '', '/');

      const onNewGameRequested = jest.fn(() => Promise.resolve());
      new Menu(fakeGame(), { onNewGameRequested });

      const newGameBtn = document.getElementById('newGameBtn');
      expect(newGameBtn.disabled).toBe(false);

      newGameBtn.click();

      expect(onNewGameRequested).toHaveBeenCalledTimes(1);
      expect(newGameBtn.disabled).toBe(true);

      await flushPromises();

      expect(newGameBtn.disabled).toBe(false);
    });

    test('schedules auto new game when request fails', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      const setTimeoutSpy = jest.spyOn(global, 'setTimeout').mockImplementation(() => 0);

      try {
        buildDom();
        history.replaceState(null, '', '/');

        const onNewGameRequested = jest.fn(() => Promise.reject(new Error('boom')));
        new Menu(fakeGame(), { onNewGameRequested });

        const autoCheckbox = document.getElementById('autoNewGame');
        autoCheckbox.checked = true;

        const newGameBtn = document.getElementById('newGameBtn');
        newGameBtn.click();

        expect(onNewGameRequested).toHaveBeenCalledTimes(1);
        expect(newGameBtn.disabled).toBe(true);

        await flushPromises();

        expect(newGameBtn.disabled).toBe(false);
        expect(setTimeoutSpy).toHaveBeenCalledTimes(1);
        expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 2000);
      } finally {
        setTimeoutSpy.mockRestore();
        consoleErrorSpy.mockRestore();
      }
    });
  });

  test('updates terrain label when a hex is selected', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const selectedHex = {
      row: 1,
      column: 2,
      isEmpty: () => true,
      getTerrain: () => ({
        name: 'open',
      }),
    };

    const menu = new Menu(fakeGame({
      getBoard: () => ({
        getSelectedHex: () => selectedHex,
        isOwnHexSelected: () => false,
        hasCombat: () => false,
      }),
    }));

    menu.updateMenu();

    expect(document.getElementById('selHexTerrain').innerHTML).toBe('Terrain: open');
  });

  test('shows no selection message when no hex is selected', () => {
    buildDom();
    history.replaceState(null, '', '/');

    new Menu(fakeGame());

    expect(document.getElementById('selHexContents').innerHTML).toBe('<em>No selection</em>');
  });

  test('shows objective details when present on selected hex', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const selectedHex = {
      row: 4,
      column: 7,
      isEmpty: () => true,
      getTerrain: () => null,
      hasObjectives: () => true,
      getObjectives: () => [
        {
          points: 3,
          displayName: 'Hold',
        },
      ],
    };

    const menu = new Menu(fakeGame({
      getBoard: () => ({
        getSelectedHex: () => selectedHex,
        isOwnHexSelected: () => false,
        hasCombat: () => false,
      }),
    }));

    menu.updateMenu();

    expect(document.getElementById('selHexObjectives').innerHTML).toBe('🚩 Hold (3 pts/turn)');
  });

  test('renders victory points with faction colors and scores on initialization', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const players = [
      {
        getName: () => 'Player 1',
        getFactions: () => [{ getCounterColor: () => '#ff0000' }],
      },
      {
        getName: () => 'Player 2',
        getFactions: () => [{ getCounterColor: () => '#0000ff' }],
      },
    ];

    new Menu(fakeGame({
      getPlayers: () => ({
        getAllPlayers: () => players,
      }),
      getScores: () => ({
        'Player 1': 3,
        'Player 2': 1,
      }),
    }));

    const rows = document.querySelectorAll('.victory-row');
    expect(rows).toHaveLength(2);

    expect(rows[0].querySelector('.victory-name').textContent).toBe('Player 1');
    expect(rows[0].querySelector('.victory-score').textContent).toBe('3');
    expect(rows[0].querySelector('.victory-swatch').style.backgroundColor).toBe('rgb(255, 0, 0)');

    expect(rows[1].querySelector('.victory-name').textContent).toBe('Player 2');
    expect(rows[1].querySelector('.victory-score').textContent).toBe('1');
    expect(rows[1].querySelector('.victory-swatch').style.backgroundColor).toBe('rgb(0, 0, 255)');
  });

  test('falls back to neutral swatch and zero score when missing data', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const players = [
      {
        getName: () => 'Player 3',
        getFactions: () => [],
      },
    ];

    const menu = new Menu(fakeGame({
      getPlayers: () => ({
        getAllPlayers: () => players,
      }),
      getScores: () => ({}),
    }));

    menu.updateMenu();

    const row = document.querySelector('.victory-row');
    expect(row.querySelector('.victory-name').textContent).toBe('Player 3');
    expect(row.querySelector('.victory-score').textContent).toBe('0');
    expect(row.querySelector('.victory-swatch').style.backgroundColor).toBe('rgb(176, 176, 176)');
  });
});
