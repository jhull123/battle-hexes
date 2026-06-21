import { eventBus as defaultEventBus } from './event-bus.js';

export class GameOverDialog {
  #dialog;
  #newGameBtn;
  #mainMenuBtn;
  #closeBtn;
  #onNewGameRequested;
  #locationRef;
  #shownGameIds = new Set();

  constructor({
    eventBus = defaultEventBus,
    onNewGameRequested,
    locationRef = window.location,
  } = {}) {
    this.#dialog = document.getElementById('gameOverDialog');
    this.#newGameBtn = document.getElementById('gameOverNewGameBtn');
    this.#mainMenuBtn = document.getElementById('gameOverMainMenuBtn');
    this.#closeBtn = document.getElementById('gameOverCloseBtn');
    this.#onNewGameRequested = onNewGameRequested;
    this.#locationRef = locationRef;

    this.#newGameBtn.addEventListener('click', () => this.#handleNewGameRequest());
    this.#mainMenuBtn.addEventListener('click', () => this.#returnToMainMenu());
    this.#closeBtn.addEventListener('click', () => this.#hide());
    eventBus.on('gameOver', (event) => this.#showOnceForGame(event.gameId));
  }

  #showOnceForGame(gameId) {
    if (this.#shownGameIds.has(gameId)) {
      return;
    }

    this.#shownGameIds.add(gameId);
    this.#show();
  }

  #show() {
    this.#dialog.style.display = 'flex';
  }

  #hide() {
    this.#dialog.style.display = 'none';
  }

  #handleNewGameRequest() {
    if (!this.#onNewGameRequested) {
      return;
    }

    this.#newGameBtn.disabled = true;
    Promise.resolve(this.#onNewGameRequested())
      .catch((err) => {
        console.error('Failed to start new game', err);
      })
      .finally(() => {
        this.#newGameBtn.disabled = false;
      });
  }

  #returnToMainMenu() {
    this.#locationRef.assign('index.html');
  }
}
