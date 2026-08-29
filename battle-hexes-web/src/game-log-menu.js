export class GameLogMenu {
  #game;
  #list;

  constructor(game) {
    this.#game = game;
    this.#list = document.getElementById('gameLogList');
  }

  setGame(game) {
    this.#game = game;
  }

  update() {
    if (!this.#list) return;
    this.#list.replaceChildren();
    for (const record of this.#game.getGameLog()) {
      const heading = document.createElement('div');
      heading.className = 'game-log-heading';
      heading.textContent = `Turn ${record.turnNumber} - ${record.playerName}`;
      this.#list.appendChild(heading);
      for (const event of record.events.reinforcements) {
        const entry = document.createElement('div');
        const label = event.outcome === 'arrived' ? 'arrived' : 'blocked';
        const units = event.unitCount === 1 ? 'unit' : 'units';
        const [q, r] = event.entryCoordinate;
        entry.textContent = `Reinforcements ${label} - ${event.unitCount} ${units} at (${q}, ${r})`;
        this.#list.appendChild(entry);
      }
    }
  }
}
