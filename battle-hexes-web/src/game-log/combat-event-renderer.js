export class CombatEventRenderer {
  render(event) {
    const entry = document.createElement('div');
    entry.className = 'game-log-combat';
    this.#appendLine(entry, 'Combat', 'game-log-combat-title');
    this.#appendParticipants(entry, 'Attacking', event.attackers);
    this.#appendParticipants(entry, 'Defending', event.defenders);
    this.#appendLine(entry, `Base odds: ${this.#odds(event.baseOdds)}`);
    this.#appendLine(entry, `Modified odds: ${this.#odds(event.modifiedOdds)}`);
    this.#appendTerrainModifier(entry, event.defenderTerrain);
    this.#appendLine(entry, `Die roll: ${event.dieRoll}`);
    this.#appendLine(entry, `Result: ${event.result.text}`);
    this.#appendLine(entry, event.result.summary);
    this.#appendUnitEffects(entry, 'Eliminated', event.eliminatedUnits);
    this.#appendUnitEffects(entry, 'Retreated', event.retreatedUnits);
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
