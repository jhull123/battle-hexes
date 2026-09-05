import { createFactionSwatch } from '../faction-swatch.js';

export class CombatEventRenderer {
  render(event, faction) {
    const entry = document.createElement('details');
    entry.className = 'game-log-combat';
    const heading = document.createElement('summary');
    heading.className = 'game-log-combat-title';
    const disclosure = document.createElement('button');
    disclosure.className = 'game-log-disclosure';
    disclosure.type = 'button';
    disclosure.setAttribute('aria-label', 'Expand combat details');
    disclosure.setAttribute('aria-expanded', 'false');
    disclosure.addEventListener('click', (clickEvent) => {
      clickEvent.preventDefault();
      clickEvent.stopPropagation();
      entry.open = !entry.open;
      disclosure.setAttribute('aria-expanded', `${entry.open}`);
      disclosure.setAttribute('aria-label', `${entry.open ? 'Collapse' : 'Expand'} combat details`);
    });
    entry.addEventListener('toggle', () => {
      disclosure.setAttribute('aria-expanded', `${entry.open}`);
      disclosure.setAttribute('aria-label', `${entry.open ? 'Collapse' : 'Expand'} combat details`);
    });
    const title = document.createElement('span');
    title.textContent = `Combat - ${event.result.text}`;
    heading.append(disclosure, createFactionSwatch(faction, 'game-log-faction-swatch'), title);
    entry.appendChild(heading);
    this.#appendParticipants(entry, 'Attacking', event.attackers);
    this.#appendParticipants(entry, 'Defending', event.defenders);
    this.#appendLine(entry, `Base odds: ${this.#odds(event.baseOdds)}`);
    this.#appendLine(entry, `Modified odds: ${this.#odds(event.modifiedOdds)}`);
    this.#appendTerrainModifier(entry, event.defenderTerrain);
    this.#appendLine(entry, `Die roll: ${event.dieRoll}`);
    this.#appendUnitEffects(entry, 'Eliminated', event.eliminatedUnits);
    return entry;
  }

  #appendTerrainModifier(parent, terrain) {
    const signedShift = terrain.oddsShift >= 0
      ? `+${terrain.oddsShift}`
      : `${terrain.oddsShift}`;
    this.#appendLine(
      parent,
      `Modified by defender terrain: ${terrain.name} (${signedShift} odds shift)`,
    );
  }

  #appendParticipants(parent, label, units) {
    const line = document.createElement('div');
    line.append(`${label}: `);
    units.forEach((unit, index) => {
      if (index > 0) line.append(', ');
      line.append(unit.name, ' ');
      const stats = document.createElement('span');
      stats.className = 'game-log-unit-stats';
      stats.textContent = `${unit.attack}-${unit.defense}-${unit.movement}`;
      line.appendChild(stats);
    });
    parent.appendChild(line);
  }

  #appendUnitEffects(parent, label, unitNames) {
    if (unitNames.length > 0) {
      this.#appendLine(parent, `${label}: ${unitNames.join(', ')}`);
    }
  }

  #appendLine(parent, text, className = '') {
    const line = document.createElement('div');
    line.className = className;
    line.textContent = text;
    parent.appendChild(line);
  }

  #odds(odds) {
    return `${odds[0]}:${odds[1]}`;
  }
}
