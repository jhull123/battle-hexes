/** @jest-environment jsdom */
import { GameLogMenu } from '../../src/game-log/game-log-menu.js';
import { Faction } from '../../src/model/faction.js';
import { Player, Players, playerTypes } from '../../src/player/player.js';

describe('GameLogMenu', () => {
  let players;

  beforeEach(() => {
    document.body.innerHTML = '<div id="gameLogList"></div>';
    players = new Players([
      new Player('Player 1', playerTypes.HUMAN, [new Faction('allies', 'Allies', '#ff0000')]),
      new Player('Player 2', playerTypes.HUMAN, [new Faction('axis', 'Axis', '#0000ff')]),
    ], 'Player 1');
  });

  test('renders the complete structured log in supplied newest-first order', () => {
    const game = {
      getPlayers: () => players,
      getGameLog: () => [
        {
          turnNumber: 4,
          playerName: 'Player 2',
          events: { reinforcements: [
            { outcome: 'arrived', unitCount: 1, entryCoordinate: [0, 16] },
          ], combat: [] },
        },
        {
          turnNumber: 3,
          playerName: 'Player 1',
          events: { reinforcements: [
            { outcome: 'blocked', unitCount: 2, entryCoordinate: [0, 0] },
          ], combat: [] },
        },
      ],
    };

    new GameLogMenu(game).update();

    expect(document.getElementById('gameLogList').textContent).toBe(
      'Turn 4 - Player 2Reinforcements arrived - 1 unit at (0, 16)'
      + 'Turn 3 - Player 1Reinforcements blocked - 2 units at (0, 0)',
    );
    expect(document.querySelectorAll('.game-log-heading')).toHaveLength(2);
  });

  test('renders collapsed combat above reinforcements without repeated result details', () => {
    const game = { getPlayers: () => players, getGameLog: () => [{
      turnNumber: 3,
      playerName: 'Player 2',
      events: {
        reinforcements: [
          { outcome: 'arrived', unitCount: 1, entryCoordinate: [0, 16] },
        ],
        combat: [{
          attackers: [
            { name: 'Unit A', attack: 4, defense: 4, movement: 2 },
            { name: 'Unit B', attack: 2, defense: 2, movement: 4 },
          ],
          defenders: [{ name: 'Unit C', attack: 3, defense: 3, movement: 3 }],
          baseOdds: [3, 1],
          modifiedOdds: [2, 1],
          defenderTerrain: { name: 'Woods', oddsShift: -1 },
          dieRoll: 4,
          result: {
            text: 'Defender Retreat 2 Hexes',
            summary: 'Unit C retreated 2 hexes.',
          },
          eliminatedUnits: [],
          retreatedUnits: ['Unit C'],
        }],
      },
    }] };

    new GameLogMenu(game).update();

    const entry = document.querySelector('.game-log-combat');
    expect(entry.tagName).toBe('DETAILS');
    expect(entry.open).toBe(false);
    expect(entry.querySelector('summary').textContent).toBe(
      'Combat - Defender Retreat 2 Hexes',
    );
    const swatch = entry.querySelector('.game-log-faction-swatch');
    expect(swatch.style.backgroundColor).toBe('rgb(0, 0, 255)');
    expect(swatch.getAttribute('aria-label')).toBe('Axis faction');
    const disclosure = entry.querySelector('.game-log-disclosure');
    disclosure.click();
    expect(entry.open).toBe(true);
    expect(disclosure.getAttribute('aria-expanded')).toBe('true');
    disclosure.click();
    expect(entry.open).toBe(false);
    expect(disclosure.getAttribute('aria-expanded')).toBe('false');
    entry.querySelector('summary').click();
    expect(entry.open).toBe(true);
    expect(entry.textContent).toContain('Attacking: Unit A 4-4-2, Unit B 2-2-4');
    expect(entry.textContent).toContain('Defending: Unit C 3-3-3');
    expect(entry.textContent).toContain('Base odds: 3:1');
    expect(entry.textContent).toContain('Modified odds: 2:1');
    expect(entry.textContent).toContain(
      'Modified by defender terrain: Woods (-1 odds shift)',
    );
    expect(entry.textContent).toContain('Die roll: 4');
    expect(entry.textContent).not.toContain('Result:');
    expect(entry.textContent).not.toContain('Unit C retreated 2 hexes.');
    expect(entry.textContent).not.toContain('Retreated:');
    expect(entry.textContent).not.toContain('Eliminated:');
    expect(entry.querySelectorAll('.game-log-unit-stats')).toHaveLength(3);
    expect(entry.nextElementSibling.textContent).toBe(
      'Reinforcements arrived - 1 unit at (0, 16)',
    );
  });

  test('renders no placeholder for an empty log', () => {
    new GameLogMenu({ getGameLog: () => [], getPlayers: () => players }).update();

    expect(document.getElementById('gameLogList').textContent).toBe('');
  });
});
