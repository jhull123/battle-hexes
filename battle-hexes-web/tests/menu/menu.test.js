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
      <div id="unitMovesLeftDiv"></div>
      <button id="newGameBtn"></button>
      <div id="gameOverLabel"></div>
      <input type="checkbox" id="autoNewGame">
      <input type="checkbox" id="showHexCoords">
      <div id="phasesList"></div>
      <button id="endPhaseBtn"></button>
      <div id="currentTurnLabel"></div>
    `;
  }

  function fakeGame() {
    return {
      getBoard: () => ({
        getSelectedHex: () => null,
        isOwnHexSelected: () => false,
        hasCombat: () => false,
      }),
      getPhases: () => ['Movement', 'Combat'],
      getCurrentPhase: () => 'Movement',
      getCurrentPlayer: () => ({ getName: () => 'P1' }),
      isGameOver: () => false,
    };
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
});
