/** @jest-environment jsdom */
import { GameLogMenu } from '../../src/game-log-menu.js';

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
          ] },
        },
        {
          turnNumber: 3,
          playerName: 'Player 1',
          events: { reinforcements: [
            { outcome: 'blocked', unitCount: 2, entryCoordinate: [0, 0] },
          ] },
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

  test('renders no placeholder for an empty log', () => {
    new GameLogMenu({ getGameLog: () => [] }).update();

    expect(document.getElementById('gameLogList').textContent).toBe('');
  });
});
