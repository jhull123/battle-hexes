import { CombatEventRenderer } from './combat-event-renderer.js';
import { ReinforcementEventRenderer } from './reinforcement-event-renderer.js';
import { DefensiveFireEventRenderer } from './defensive-fire-event-renderer.js';
import { createPlayerSwatch } from '../faction-swatch.js';

export class GameLogMenu {
  #game;
  #list;
  #combatRenderer;
  #reinforcementRenderer;
  #defensiveFireRenderer;

  constructor(game) {
    this.#game = game;
    this.#list = document.getElementById('gameLogList');
    this.#combatRenderer = new CombatEventRenderer();
    this.#reinforcementRenderer = new ReinforcementEventRenderer();
    this.#defensiveFireRenderer = new DefensiveFireEventRenderer();
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
    const player = this.#playerForName(record.playerName);
    heading.append(
      createPlayerSwatch(player, 'game-log-player-swatch'),
      `Turn ${record.turnNumber} - ${record.playerName}`,
    );
    this.#list.appendChild(heading);
    this.#appendEvents(record.events.combat, this.#combatRenderer);
    this.#appendEvents(
      record.events.defensiveFire ?? [],
      this.#defensiveFireRenderer,
    );
    this.#appendEvents(record.events.reinforcements, this.#reinforcementRenderer);
  }

  #appendEvents(events, renderer, ...renderArgs) {
    for (const event of events) {
      this.#list.appendChild(renderer.render(event, ...renderArgs));
    }
  }

  #playerForName(playerName) {
    return this.#game.getPlayers().getAllPlayers()
      .find((candidate) => candidate.getName() === playerName);
  }
}
