import { createFactionSwatch } from './faction-swatch.js';

export class ReinforcementsMenu {
  #game;
  #menu;
  #divider;
  #list;

  constructor(game) {
    this.#game = game;
    this.#menu = document.getElementById('reinforcementsMenu');
    this.#divider = document.getElementById('reinforcementsDivider');
    this.#list = document.getElementById('reinforcementsList');
  }

  setGame(game) {
    this.#game = game;
  }

  updateReinforcements() {
    if (!this.#menu || !this.#list) return;
    const reinforcements = this.#game.getReinforcements?.();
    if (!reinforcements) {
      this.#setVisible(false);
      return;
    }
    this.#setVisible(true);
    this.#renderPending(reinforcements.pending);
  }

  #setVisible(visible) {
    this.#menu.style.display = visible ? '' : 'none';
    if (this.#divider) this.#divider.style.display = visible ? '' : 'none';
  }

  #renderPending(pending) {
    this.#list.replaceChildren();
    if (pending.length === 0) {
      this.#list.textContent = 'None';
      return;
    }
    for (const grouping of this.#groupings(pending)) {
      this.#appendGrouping(grouping);
    }
  }

  #appendGrouping(grouping) {
    const turn = document.createElement('div');
    turn.className = 'reinforcement-turn';
    turn.textContent = grouping.label;
    this.#list.append(turn);
    for (const player of this.#game.getPlayers().getAllPlayers()) {
      this.#appendPlayerGroups(player, grouping.groups);
    }
  }

  #appendPlayerGroups(player, groupingGroups) {
    const groups = groupingGroups.filter(
      (group) => group.playerName === player.getName(),
    );
    if (groups.length === 0) return;
    const heading = document.createElement('div');
    heading.className = 'reinforcement-player';
    heading.textContent = player.getName();
    this.#list.append(heading);
    for (const group of groups) {
      group.units.forEach((unit) => this.#appendUnit(unit));
    }
  }

  #groupings(pending) {
    const turnNumber = this.#game.getTurnNumber();
    const keys = [...new Set(pending.map(
      (group) => this.#groupingKey(group, turnNumber),
    ))];
    keys.sort((left, right) => this.#compareGroupingKeys(left, right));
    return keys.map((key) => this.#createGrouping(key, pending, turnNumber));
  }

  #groupingKey(group, turnNumber) {
    return group.status === 'delayed'
      ? `${turnNumber}:delayed`
      : `${group.arrivalTurn}:scheduled`;
  }

  #compareGroupingKeys(left, right) {
    const [leftTurn, leftStatus] = left.split(':');
    const [rightTurn] = right.split(':');
    if (+leftTurn !== +rightTurn) return +leftTurn - +rightTurn;
    return leftStatus === 'scheduled' ? -1 : 1;
  }

  #createGrouping(key, pending, turnNumber) {
    const [turn, status] = key.split(':');
    return {
      label: `Turn ${turn}${status === 'delayed' ? ' (Delayed)' : ''}`,
      groups: pending.filter(
        (group) => this.#groupingKey(group, turnNumber) === key,
      ),
    };
  }

  #appendUnit(unit) {
    const faction = this.#findFaction(unit.factionId);
    const row = document.createElement('div');
    row.className = 'selected-unit-row';
    row.append(createFactionSwatch(faction, 'selected-unit-swatch'), this.#createUnitLabel(unit));
    this.#list.append(row);
  }

  #findFaction(factionId) {
    return this.#game.getPlayers().getAllPlayers()
      .flatMap((player) => player.getFactions())
      .find((faction) => faction.getId() === factionId);
  }

  #createUnitLabel(unit) {
    const label = document.createElement('span');
    label.textContent = `${unit.name} `;
    const coordinate = document.createElement('span');
    coordinate.className = 'selected-unit-moves';
    coordinate.textContent = `(${unit.entryCoordinate[0]}, ${unit.entryCoordinate[1]})`;
    label.append(coordinate);
    return label;
  }
}
