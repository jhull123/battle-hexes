import { CombatEventRenderer } from './combat-event-renderer.js';
import { ReinforcementEventRenderer } from './reinforcement-event-renderer.js';

export class GameLogMenu {
  #game;
  #list;
  #combatRenderer;
  #reinforcementRenderer;

  constructor(game) {
    this.#game = game;
    this.#list = document.getElementById('gameLogList');
    this.#combatRenderer = new CombatEventRenderer();
    this.#reinforcementRenderer = new ReinforcementEventRenderer();
  }

  setGame(game) {
    this.#game = game;
  }

  update() {
    if (!this.#list) return;
    this.#list.replaceChildren();
    for (const record of this.#game.getGameLog()) {
      this.#renderRecord(record);
    }
  }

  #renderRecord(record) {
    const heading = document.createElement('div');
    heading.className = 'game-log-heading';
    heading.textContent = `Turn ${record.turnNumber} - ${record.playerName}`;
    this.#list.appendChild(heading);
    this.#appendEvents(record.events.combat, this.#combatRenderer);
    this.#appendEvents(record.events.reinforcements, this.#reinforcementRenderer);
  }

  #appendEvents(events, renderer) {
    for (const event of events) {
      this.#list.appendChild(renderer.render(event));
    }
  }
}
