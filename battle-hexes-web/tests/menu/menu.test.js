/** @jest-environment jsdom */
import axios from 'axios';
import { Menu } from '../../src/menu';
import { eventBus } from '../../src/event-bus.js';
import { API_URL } from '../../src/model/battle-api.js';

jest.mock('axios');

jest.mock('../../src/event-bus.js', () => ({
  eventBus: {
    emit: jest.fn(),
    on: jest.fn(),
  },
}));

describe('auto new game persistence', () => {
  const flushPromises = () => new Promise((resolve) => queueMicrotask(resolve));

  function buildDom() {
    document.body.innerHTML = `
      <div id="selHexContents"></div>
      <div id="selHexCoord"></div>
      <h4 id="selHexUnitsHeading"></h4>
      <div id="selHexTerrain"></div>
      <h4 id="selHexTerrainHeading"></h4>
      <div id="selHexObjectives"></div>
      <div id="reactionStatus"></div>
      <div id="unitMovesLeftDiv"></div>
      <button id="newGameBtn"></button>
      <div id="gameOverLabel"></div>
      <input type="checkbox" id="autoNewGame">
      <input type="checkbox" id="showHexCoords">
      <div id="phasesList"></div>
      <button id="endPhaseBtn"></button>
      <div id="currentTurnLabel"></div>
      <div id="victoryTurnLabel"></div>
      <div id="victoryPointsList"></div>
      <h3 id="scenarioOverviewHeading"></h3>
      <p id="scenarioOverviewDescription"></p>
      <h4 id="scenarioVictoryHeading"></h4>
      <p id="scenarioVictoryDescription"></p>
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
      getScenarioId: () => 'elim_1',
    };

    return { ...baseGame, ...overrides };
  }

  beforeEach(() => {
    eventBus.emit.mockClear();
    eventBus.on.mockClear();
    window.localStorage.clear();
    axios.post.mockReset();
    axios.get.mockReset();
    axios.get.mockResolvedValue({ data: [] });
  });

  test('shows scenario heading from name with description and victory conditions', async () => {
    buildDom();

    axios.get.mockResolvedValue({
      data: [{
        id: 'elim_1',
        name: 'Elimination One',
        description: 'Secure all objectives before the turn limit.',
        victory: {
          description: 'Control every objective at the end of any turn.',
        },
      }],
    });

    new Menu(fakeGame());
    await flushPromises();

    expect(document.getElementById('scenarioOverviewHeading').textContent).toBe('Elimination One');
    expect(document.getElementById('scenarioOverviewDescription').textContent).toBe('Secure all objectives before the turn limit.');
    expect(document.getElementById('scenarioVictoryHeading').style.display).toBe('');
    expect(document.getElementById('scenarioVictoryDescription').textContent).toBe('Control every objective at the end of any turn.');
  });

  test('shows defensive fire messages from movement-phase reactions', async () => {
    buildDom();

    new Menu(fakeGame());
    await flushPromises();

    const defensiveFireListener = eventBus.on.mock.calls.find(
      ([eventName]) => eventName === 'defensiveFireResolved'
    )?.[1];

    defensiveFireListener([
      { message: 'Defensive fire forced the target to retreat to (0, 1).' },
      { message: 'Defensive fire had no effect.' },
    ]);

    expect(document.getElementById('reactionStatus').textContent).toBe(
      'Defensive fire forced the target to retreat to (0, 1). Defensive fire had no effect.'
    );
  });

  test('falls back to scenario id and hides optional sections when details are missing', async () => {
    buildDom();

    axios.get.mockResolvedValue({
      data: [{
        id: 'elim_1',
      }],
    });

    new Menu(fakeGame());
    await flushPromises();

    expect(document.getElementById('scenarioOverviewHeading').textContent).toBe('elim_1');
    expect(document.getElementById('scenarioOverviewDescription').style.display).toBe('none');
    expect(document.getElementById('scenarioOverviewDescription').textContent).toBe('');
    expect(document.getElementById('scenarioVictoryHeading').style.display).toBe('none');
    expect(document.getElementById('scenarioVictoryDescription').style.display).toBe('none');
    expect(document.getElementById('scenarioVictoryDescription').textContent).toBe('');
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

  test('shows selected hex coord, units fallback, terrain move cost, and headings', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const selectedHex = {
      row: 1,
      column: 2,
      getUnits: () => [],
      getTerrain: () => ({
        name: 'open',
        moveCost: 1,
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

    expect(document.getElementById('selHexCoord').innerHTML).toBe('Coords: (1, 2)');
    expect(document.getElementById('selHexContents').innerHTML).toBe('<em>None</em>');
    expect(document.getElementById('selHexTerrain').innerHTML).toBe('Open (cost=1)');
    expect(document.getElementById('selHexUnitsHeading').style.display).toBe('');
    expect(document.getElementById('selHexTerrainHeading').style.display).toBe('');
  });


  test('shows selected hex unit details with echelon when units are present', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const selectedHex = {
      row: 4,
      column: 9,
      getUnits: () => [{
        getName: () => 'Airborne Inf. A',
        getAttack: () => 3,
        getDefense: () => 2,
        getMovement: () => 5,
        getEchelon: () => 'platoon',
        getMovesRemaining: () => 0,
      }],
      getTerrain: () => ({
        name: 'open',
        moveCost: 1,
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

    const unitRow = document.querySelector('#selHexContents .selected-unit-row');
    expect(unitRow.textContent).toBe('Airborne Inf. A (moves 0)');
    expect(unitRow.querySelector('.selected-unit-label').title).toBe('platoon, 3-2-5');
    expect(unitRow.querySelector('.selected-unit-swatch').style.backgroundColor).toBe('rgb(176, 176, 176)');
  });

  test('omits echelon in selected hex unit details when not present', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const selectedHex = {
      row: 4,
      column: 9,
      getUnits: () => [{
        getName: () => 'Airborne Inf. A',
        getAttack: () => 3,
        getDefense: () => 2,
        getMovement: () => 5,
        getEchelon: () => null,
        getMovesRemaining: () => 0,
        getOwningPlayer: () => ({
          getFactions: () => [{ getCounterColor: () => '#ff0000' }],
        }),
      }],
      getTerrain: () => ({
        name: 'open',
        moveCost: 1,
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

    const unitRow = document.querySelector('#selHexContents .selected-unit-row');
    expect(unitRow.textContent).toBe('Airborne Inf. A (moves 0)');
    expect(unitRow.querySelector('.selected-unit-label').title).toBe('3-2-5');
    expect(unitRow.querySelector('.selected-unit-swatch').style.backgroundColor).toBe('rgb(255, 0, 0)');
  });

  test('shows no selection message when no hex is selected', () => {
    buildDom();
    history.replaceState(null, '', '/');

    new Menu(fakeGame());

    expect(document.getElementById('selHexCoord').innerHTML).toBe('<em>No selection</em>');
    expect(document.getElementById('selHexUnitsHeading').style.display).toBe('none');
    expect(document.getElementById('selHexTerrainHeading').style.display).toBe('none');
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
      getCurrentPlayer: () => ({
        getName: () => 'Player 1',
        isHuman: () => true,
        play: jest.fn(),
      }),
      getScores: () => ({
        'Player 1': 3,
        'Player 2': 1,
      }),
    }));

    const rows = document.querySelectorAll('.victory-row');
    expect(rows).toHaveLength(2);
    expect(document.getElementById('victoryTurnLabel').textContent).toBe('Turn 1 / ∞');

    expect(rows[0].querySelector('.victory-name').textContent).toBe('Player 1');
    expect(rows[0].querySelector('.victory-score').textContent).toBe('3');
    expect(rows[0].querySelector('.victory-swatch').style.backgroundColor).toBe('rgb(255, 0, 0)');
    expect(rows[0].classList.contains('victory-row-current')).toBe(true);
    expect(rows[0].querySelector('.victory-turn-badge').textContent).toBe('Turn');
    expect(rows[0].querySelector('.victory-turn-badge').hidden).toBe(false);

    expect(rows[1].querySelector('.victory-name').textContent).toBe('Player 2');
    expect(rows[1].querySelector('.victory-score').textContent).toBe('1');
    expect(rows[1].querySelector('.victory-swatch').style.backgroundColor).toBe('rgb(0, 0, 255)');
    expect(rows[1].classList.contains('victory-row-current')).toBe(false);
    expect(rows[1].querySelector('.victory-turn-badge')).toBeNull();
  });


  test('freezes displayed turn at the limit when game state has advanced past it', () => {
    buildDom();
    history.replaceState(null, '', '/');

    new Menu(fakeGame({
      getTurnLimit: () => 9,
      getTurnNumber: () => 10,
    }));

    expect(document.getElementById('victoryTurnLabel').textContent).toBe('Turn 9 / 9');
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

  test('updates victory points after end of movement response', async () => {
    buildDom();
    history.replaceState(null, '', '/');

    const players = [
      {
        getName: () => 'Player 1',
        getFactions: () => [{ getCounterColor: () => '#ff0000' }],
      },
    ];

    let currentScores = { 'Player 1': 0 };
    const game = fakeGame({
      getPlayers: () => ({
        getAllPlayers: () => players,
      }),
      getScores: () => ({ ...currentScores }),
      updateScores: (scores) => {
        currentScores = { ...scores };
      },
      getCurrentPhase: () => 'Movement',
      endPhase: () => false,
      getBoard: () => ({
        sparseBoard: () => ({}),
        getSelectedHex: () => null,
        isOwnHexSelected: () => false,
        hasCombat: () => false,
      }),
    });

    axios.post.mockResolvedValue({
      data: {
        scores: {
          'Player 1': 4,
        },
      },
    });

    const menu = new Menu(game);
    expect(document.querySelector('.victory-score').textContent).toBe('0');

    menu.doEndPhase();
    await flushPromises();

    expect(document.querySelector('.victory-score').textContent).toBe('4');
  });

  test('posts end-turn board state captured before endPhase resets moves', async () => {
    buildDom();
    history.replaceState(null, '', '/');

    const preResetPayload = {
      units: [{ id: 'unit-1', defensive_fire_available: false }],
    };
    const postResetPayload = {
      units: [{ id: 'unit-1', defensive_fire_available: true }],
    };
    let movesReset = false;
    const currentPlayer = {
      getName: () => 'Player 1',
      isHuman: () => true,
      play: jest.fn(),
    };

    const game = fakeGame({
      getCurrentPhase: () => 'End Turn',
      getCurrentPlayer: () => currentPlayer,
      endPhase: () => {
        movesReset = true;
        return true;
      },
      getBoard: () => ({
        sparseBoard: () => (movesReset ? postResetPayload : preResetPayload),
        getSelectedHex: () => null,
        isOwnHexSelected: () => false,
        hasCombat: () => false,
      }),
    });

    axios.post.mockResolvedValue({ data: {} });

    const menu = new Menu(game);
    menu.doEndPhase();
    await flushPromises();

    expect(axios.post).toHaveBeenCalledWith(
      `${API_URL}/games/game-id/end-turn`,
      preResetPayload
    );
    expect(axios.post).not.toHaveBeenCalledWith(
      `${API_URL}/games/game-id/end-turn`,
      postResetPayload
    );
  });

  test('redraws immediately after a turn switch so refreshed defensive fire icons are visible', () => {
    buildDom();
    history.replaceState(null, '', '/');

    const game = fakeGame({
      getCurrentPhase: () => 'End Turn',
      endPhase: () => true,
      getBoard: () => ({
        sparseBoard: () => ({}),
        getSelectedHex: () => null,
        isOwnHexSelected: () => false,
        hasCombat: () => false,
      }),
    });

    axios.post.mockResolvedValue({ data: {} });

    const menu = new Menu(game);
    eventBus.emit.mockClear();

    menu.doEndPhase();

    expect(eventBus.emit).toHaveBeenCalledWith('redraw');
  });

  test('moves turn badge and highlight when current player changes', () => {
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

    let currentPlayerName = 'Player 1';
    const menu = new Menu(fakeGame({
      getPlayers: () => ({
        getAllPlayers: () => players,
      }),
      getCurrentPlayer: () => ({
        getName: () => currentPlayerName,
        isHuman: () => true,
        play: jest.fn(),
      }),
      getScores: () => ({
        'Player 1': 3,
        'Player 2': 1,
      }),
    }));

    let rows = document.querySelectorAll('.victory-row');
    expect(rows[0].classList.contains('victory-row-current')).toBe(true);
    expect(rows[0].querySelector('.victory-turn-badge').hidden).toBe(false);
    expect(rows[1].classList.contains('victory-row-current')).toBe(false);
    expect(rows[1].querySelector('.victory-turn-badge')).toBeNull();

    currentPlayerName = 'Player 2';
    menu.updateMenu();

    rows = document.querySelectorAll('.victory-row');
    expect(rows[0].classList.contains('victory-row-current')).toBe(false);
    expect(rows[0].querySelector('.victory-turn-badge')).toBeNull();
    expect(rows[1].classList.contains('victory-row-current')).toBe(true);
    expect(rows[1].querySelector('.victory-turn-badge').hidden).toBe(false);
  });
});
