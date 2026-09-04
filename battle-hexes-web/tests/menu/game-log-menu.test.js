/** @jest-environment jsdom */
import { GameLogMenu } from '../../src/game-log/game-log-menu.js';

describe('GameLogMenu', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="gameLogList"></div>';
  });

  test('renders the complete structured log in supplied newest-first order', () => {
    const game = {
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

  test('renders detailed combat blocks and omits empty effect lines', () => {
    const game = { getGameLog: () => [{
      turnNumber: 3,
      playerName: 'Player 2',
      events: {
        reinforcements: [],
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
    expect(entry.textContent).toContain('Combat');
    expect(entry.textContent).toContain('Attacking: Unit A 4-4-2, Unit B 2-2-4');
    expect(entry.textContent).toContain('Defending: Unit C 3-3-3');
    expect(entry.textContent).toContain('Base odds: 3:1');
    expect(entry.textContent).toContain('Modified odds: 2:1');
    expect(entry.textContent).toContain(
      'Modified by defender terrain: Woods (-1 odds shift)',
    );
    expect(entry.textContent).toContain('Die roll: 4');
    expect(entry.textContent).toContain('Result: Defender Retreat 2 Hexes');
    expect(entry.textContent).toContain('Unit C retreated 2 hexes.');
    expect(entry.textContent).toContain('Retreated: Unit C');
    expect(entry.textContent).not.toContain('Eliminated:');
    expect(entry.querySelectorAll('.game-log-unit-stats')).toHaveLength(3);
  });

  test('renders no placeholder for an empty log', () => {
    new GameLogMenu({ getGameLog: () => [] }).update();

    expect(document.getElementById('gameLogList').textContent).toBe('');
  });
});
