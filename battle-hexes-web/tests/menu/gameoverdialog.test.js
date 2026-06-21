/** @jest-environment jsdom */

import { GameOverDialog } from '../../src/gameoverdialog.js';

describe('game over dialog', () => {
  const flushPromises = () => new Promise((resolve) => queueMicrotask(resolve));

  function buildDom() {
    document.body.innerHTML = `
      <div id="gameOverDialog" style="display: none;">
        <h2 id="gameOverDialogTitle">Game Over</h2>
        <p id="gameOverDialogMessage">The game is over.</p>
        <button id="gameOverNewGameBtn">New Game</button>
        <button id="gameOverMainMenuBtn">Main Menu</button>
        <button id="gameOverCloseBtn">Close</button>
      </div>
    `;
  }

  function fakeEventBus() {
    return {
      on: jest.fn(),
    };
  }

  function gameOverListener(eventBus) {
    return eventBus.on.mock.calls.find(([eventName]) => eventName === 'gameOver')[1];
  }

  test('shows generic game over dialog when the game over event is emitted', () => {
    buildDom();
    const eventBus = fakeEventBus();

    new GameOverDialog({ eventBus });
    gameOverListener(eventBus)({ gameId: 'game-id' });

    expect(document.getElementById('gameOverDialog').style.display).toBe('flex');
    expect(document.getElementById('gameOverDialogTitle').textContent).toBe('Game Over');
    expect(document.getElementById('gameOverDialogMessage').textContent).toBe('The game is over.');
  });

  test('does not reopen after it is closed for the same game ending', () => {
    buildDom();
    const eventBus = fakeEventBus();

    new GameOverDialog({ eventBus });
    const listener = gameOverListener(eventBus);
    listener({ gameId: 'game-id' });
    document.getElementById('gameOverCloseBtn').click();

    expect(document.getElementById('gameOverDialog').style.display).toBe('none');

    listener({ gameId: 'game-id' });

    expect(document.getElementById('gameOverDialog').style.display).toBe('none');
  });

  test('opens for a different game ending', () => {
    buildDom();
    const eventBus = fakeEventBus();

    new GameOverDialog({ eventBus });
    const listener = gameOverListener(eventBus);
    listener({ gameId: 'game-id' });
    document.getElementById('gameOverCloseBtn').click();
    listener({ gameId: 'next-game-id' });

    expect(document.getElementById('gameOverDialog').style.display).toBe('flex');
  });

  test('new game button uses the supplied new game workflow', async () => {
    buildDom();
    const eventBus = fakeEventBus();
    const onNewGameRequested = jest.fn(() => Promise.resolve());

    new GameOverDialog({ eventBus, onNewGameRequested });
    document.getElementById('gameOverNewGameBtn').click();

    expect(onNewGameRequested).toHaveBeenCalledTimes(1);
    expect(document.getElementById('gameOverNewGameBtn').disabled).toBe(true);

    await flushPromises();

    expect(document.getElementById('gameOverNewGameBtn').disabled).toBe(false);
  });

  test('main menu button returns to the title screen', () => {
    buildDom();
    const eventBus = fakeEventBus();
    const locationRef = { assign: jest.fn() };

    new GameOverDialog({ eventBus, locationRef });
    document.getElementById('gameOverMainMenuBtn').click();

    expect(locationRef.assign).toHaveBeenCalledWith('index.html');
  });
});
