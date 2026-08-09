import { eventBus as defaultEventBus } from './event-bus.js';

export class GameOverDialog {
  #dialog;
  #newGameBtn;
  #mainMenuBtn;
  #closeBtn;
  #title;
  #message;
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
    this.#title = document.getElementById('gameOverDialogTitle');
    this.#message = document.getElementById('gameOverDialogMessage');
    this.#onNewGameRequested = onNewGameRequested;
    this.#locationRef = locationRef;

    this.#newGameBtn.addEventListener('click', () => this.#handleNewGameRequest());
    this.#mainMenuBtn.addEventListener('click', () => this.#returnToMainMenu());
    this.#closeBtn.addEventListener('click', () => this.#hide());
    eventBus.on('gameOver', (event) => this.#showOnceForGame(event));
  }

  #showOnceForGame(event) {
    const gameId = event?.gameId;
    if (this.#shownGameIds.has(gameId)) {
      return;
    }

    this.#shownGameIds.add(gameId);
    this.#populate(event?.gameStatus);
    this.#show();
  }

  #populate(gameStatus) {
    const suppliedMessage = gameStatus?.message;
    const winner = gameStatus?.winner;
    const winnerName = gameStatus?.winnerPlayerName ?? (typeof winner === 'string' ? winner : winner?.name);
    const messageParts = [
      typeof suppliedMessage === 'string' && suppliedMessage.trim().length > 0
        ? suppliedMessage
        : 'The game is over.',
    ];

    if (typeof winnerName === 'string' && winnerName.trim().length > 0) {
      messageParts.push(`Winner: ${winnerName}`);
    }

    this.#title.textContent = 'Game Over';
    this.#message.textContent = messageParts.join(' ');
  }

  #show() {
    this.#dialog.style.display = 'flex';
  }

  #hide() {
    this.#dialog.style.display = 'none';
  }

  #handleNewGameRequest() {
    this.#hide();

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
