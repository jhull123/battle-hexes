import { Board } from "../../src/model/board";
import { Game } from "../../src/model/game";
import { Player, Players } from "../../src/player/player";

let game;
const phases = ['Movement', 'Combat'];
const player1 = new Player('Player 1');
const player2 = new Player('Player 2');
const players = new Players([player1, player2]);

beforeEach(() => {
  game = new Game('game-id', phases, players, new Board(10, 10));
});

describe('constructor', () => {
  test('constructor initializes current phase and player', () => {
    expect(game.getCurrentPhase()).toBe(phases[0]);
    expect(game.getCurrentPlayer()).toEqual(player1);
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