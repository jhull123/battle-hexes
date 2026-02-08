const mockResolveCombat = jest.fn().mockResolvedValue({});
jest.mock("../../src/model/combat-resolver", () => ({
  CombatResolver: jest.fn().mockImplementation(() => ({
    resolveCombat: mockResolveCombat,
  })),
}));

import { Board } from "../../src/model/board";
import { Game } from "../../src/model/game";
import { Faction } from "../../src/model/faction";
import { Unit } from "../../src/model/unit";
import { Player, Players } from "../../src/player/player";

let game;
const phases = ['Movement', 'Combat'];
const player1 = new Player('Player 1');
const player2 = new Player('Player 2');
const players = new Players([player1, player2]);

beforeEach(() => {
  mockResolveCombat.mockReset();
  mockResolveCombat.mockResolvedValue({});
  game = new Game('game-id', phases, players, new Board(10, 10));
});

describe('constructor', () => {
  test('constructor initializes current phase and player', () => {
    expect(game.getCurrentPhase()).toBe(phases[0]);
    expect(game.getCurrentPlayer()).toEqual(player1);
  });
});

describe('configuration metadata', () => {
  test('exposes scenario and player type identifiers when provided', () => {
    const configuredGame = new Game(
      'configured-id',
      phases,
      players,
      new Board(10, 10),
      {
        scenarioId: 'elem_9',
        playerTypeIds: ['human', 'q-learning'],
      },
    );

    expect(configuredGame.getScenarioId()).toBe('elem_9');
    expect(configuredGame.getPlayerTypeIds()).toEqual(['human', 'q-learning']);
  });

  test('returns null when configuration metadata is missing or invalid', () => {
    const configuredGame = new Game(
      'configured-id',
      phases,
      players,
      new Board(10, 10),
      {
        scenarioId: '   ',
        playerTypeIds: ['human', ''],
      },
    );

    expect(configuredGame.getScenarioId()).toBeNull();
    expect(configuredGame.getPlayerTypeIds()).toBeNull();
  });

  test('player type identifiers are defensively copied', () => {
    const configuredGame = new Game(
      'configured-id',
      phases,
      players,
      new Board(10, 10),
      {
        scenarioId: 'elim_1',
        playerTypeIds: ['human', 'random'],
      },
    );

    const ids = configuredGame.getPlayerTypeIds();
    ids.push('extra');

    expect(configuredGame.getPlayerTypeIds()).toEqual(['human', 'random']);
  });

  test('scores are exposed and defensively copied', () => {
    const configuredGame = new Game(
      'configured-id',
      phases,
      players,
      new Board(10, 10),
      {
        scores: {
          'Player 1': 4,
        },
      },
    );

    expect(configuredGame.getScores()).toEqual({ 'Player 1': 4 });

    const scores = configuredGame.getScores();
    scores['Player 2'] = 2;

    expect(configuredGame.getScores()).toEqual({ 'Player 1': 4 });
  });
});

describe('endPhase', () => {
  test('moves to combat when there is combat', () => {
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(true);
    const switched = game.endPhase();
    expect(switched).toBe(false);
    expect(game.getCurrentPhase()).toBe(phases[1]);
    expect(game.getCurrentPlayer()).toEqual(player1);
  });

  test('skips combat and moves to next player when none', () => {
    jest.spyOn(game.getBoard(), 'hasCombat').mockReturnValue(false);
    const switched = game.endPhase();
    expect(switched).toBe(true);
    expect(game.getCurrentPhase()).toBe(phases[0]);
    expect(game.getCurrentPlayer()).toEqual(player2);
  });
});

describe('resolveCombat', () => {
  test('updates scores from combat response', async () => {
    mockResolveCombat.mockResolvedValueOnce({ scores: { 'Player 1': 7 } });

    await game.resolveCombat();

    expect(mockResolveCombat).toHaveBeenCalled();
    expect(game.getScores()).toEqual({ 'Player 1': 7 });
  });
});

describe('isGameOver', () => {
  test('returns false when multiple players have units', () => {
    const f1 = new Faction('f1', 'f1', '#f00');
    const f2 = new Faction('f2', 'f2', '#0f0');
    f1.setOwningPlayer(player1);
    f2.setOwningPlayer(player2);

    const u1 = new Unit('u1', 'Unit1', f1, null, 1, 1, 1);
    const u2 = new Unit('u2', 'Unit2', f2, null, 1, 1, 1);
    game.getBoard().addUnit(u1, 0, 0);
    game.getBoard().addUnit(u2, 0, 1);

    expect(game.isGameOver()).toBe(false);
  });

  test('returns true when only one player has units', () => {
    const f1 = new Faction('f1', 'f1', '#f00');
    f1.setOwningPlayer(player1);
    const u1 = new Unit('u1', 'Unit1', f1, null, 1, 1, 1);
    game.getBoard().addUnit(u1, 0, 0);

    expect(game.isGameOver()).toBe(true);
  });

  test('returns true after a unit is eliminated leaving one player', () => {
    const f1 = new Faction('f1', 'f1', '#f00');
    const f2 = new Faction('f2', 'f2', '#0f0');
    f1.setOwningPlayer(player1);
    f2.setOwningPlayer(player2);

    const u1 = new Unit('u1', 'Unit1', f1, null, 1, 1, 1);
    const u2 = new Unit('u2', 'Unit2', f2, null, 1, 1, 1);
    game.getBoard().addUnit(u1, 0, 0);
    game.getBoard().addUnit(u2, 0, 1);

    game.getBoard().removeUnit(u2);

    expect(game.isGameOver()).toBe(true);
  });
});
