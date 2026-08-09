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


  test('tracks turn number and optional turn limit', () => {
    const configuredGame = new Game(
      'configured-id',
      phases,
      players,
      new Board(10, 10),
      {
        turnLimit: 9,
        turnNumber: 2,
      },
    );

    expect(configuredGame.getTurnLimit()).toBe(9);
    expect(configuredGame.getTurnNumber()).toBe(2);

    configuredGame.updateTurnState({ turnLimit: null, turnNumber: 3 });
    expect(configuredGame.getTurnLimit()).toBeNull();
    expect(configuredGame.getTurnNumber()).toBe(3);
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

describe('authoritative turn state', () => {
  test('resets movement when the backend changes the active player', () => {
    const firstPlayer = new Player('First');
    const nextPlayer = new Player('Next');
    const turnPlayers = new Players([firstPlayer, nextPlayer]);
    const board = new Board(2, 2);
    const faction = new Faction('next', 'Next faction', '#00f');
    faction.setOwningPlayer(nextPlayer);
    const unit = new Unit('u1', 'Unit', faction, null, 1, 1, 2);
    board.addUnit(unit, 0, 0);
    unit.move(board.getHex(0, 0), []);
    unit.move(board.getHex(0, 0), []);
    const turnGame = new Game('turn-state', phases, turnPlayers, board);

    turnGame.applyApiState({ activePlayer: 'Next' });

    expect(turnGame.getCurrentPlayer()).toBe(nextPlayer);
    expect(unit.getMovesRemaining()).toBe(2);
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

  test('resets movement for the new current player and defensive fire for the previous player', () => {
    const turnPhases = ['End Turn'];
    const turnPlayer1 = new Player('Player 1');
    const turnPlayer2 = new Player('Player 2');
    const turnPlayers = new Players([turnPlayer1, turnPlayer2]);
    const board = new Board(10, 10);
    const turnGame = new Game('turn-game-id', turnPhases, turnPlayers, board);

    const faction1 = new Faction('f1', 'Faction 1', '#f00');
    const faction2 = new Faction('f2', 'Faction 2', '#0f0');
    faction1.setOwningPlayer(turnPlayer1);
    faction2.setOwningPlayer(turnPlayer2);

    const unit1 = new Unit('u1', 'Unit1', faction1, null, 1, 1, 2);
    const unit2 = new Unit('u2', 'Unit2', faction2, null, 1, 1, 2);
    board.addUnit(unit1, 0, 0);
    board.addUnit(unit2, 0, 1);

    unit1.move(board.getHex(0, 0), []);
    unit2.move(board.getHex(0, 1), []);
    expect(unit1.hasDefensiveFire()).toBe(false);
    expect(unit2.hasDefensiveFire()).toBe(false);
    expect(unit1.getMovesRemaining()).toBe(1);
    expect(unit2.getMovesRemaining()).toBe(1);

    const switched = turnGame.endPhase();

    expect(switched).toBe(true);
    expect(turnGame.getCurrentPhase()).toBe('End Turn');
    expect(turnGame.getCurrentPlayer()).toEqual(turnPlayer2);
    expect(unit1.getMovesRemaining()).toBe(1);
    expect(unit2.getMovesRemaining()).toBe(2);
    expect(unit1.hasDefensiveFire()).toBe(false);
    expect(unit2.hasDefensiveFire()).toBe(true);
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


  test('resolves firing faction from unit id in board state', () => {
    const faction = new Faction('f1', 'Faction 1', '#f00', {
      defensiveFire: { effect: 'f1_effect.ogg' },
    });
    faction.setOwningPlayer(player1);
    const unit = new Unit('u1', 'Unit1', faction, null, 1, 1, 2);

    game.getBoard().addUnit(unit, 0, 0);

    expect(game.getFactionForUnitId('u1')).toBe(faction);
    expect(game.getFactionForUnitId('missing')).toBeNull();
  });

describe('game status', () => {
  test('is not over when backend status is in progress regardless of local board state', () => {
    game.updateGameStatus({ state: 'in_progress' });

    expect(game.isGameOver()).toBe(false);
  });

  test('is over only when backend status is completed', () => {
    game.updateGameStatus({ state: 'completed', message: 'Done.' });

    expect(game.isGameOver()).toBe(true);
    expect(game.getGameStatus()).toEqual({ state: 'completed', message: 'Done.' });
  });

  test('does not infer game over from turn limits or remaining unit owners', () => {
    const limitedGame = new Game('game-id', phases, players, new Board(10, 10), {
      turnLimit: 1,
      turnNumber: 2,
      gameStatus: { state: 'in_progress' },
    });

    const f1 = new Faction('f1', 'f1', '#f00');
    f1.setOwningPlayer(player1);
    limitedGame.getBoard().addUnit(new Unit('u1', 'Unit1', f1, null, 1, 1, 1), 0, 0);

    expect(limitedGame.isGameOver()).toBe(false);
  });
});
