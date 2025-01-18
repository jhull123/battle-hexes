import { Board } from "../../src/model/board";
import { Game } from "../../src/model/game";
import { Player, Players } from "../../src/model/player";

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
  test('endPhase moves to next phase when turn is not over', () => {
    game.endPhase();
    expect(game.getCurrentPhase()).toBe(phases[1]);
    expect(game.getCurrentPlayer()).toEqual(player1);
  });

  test('endPhase moves to next player when turn is over', () => {
    game.endPhase();
    game.endPhase();
    expect(game.getCurrentPhase()).toBe(phases[0]);
    expect(game.getCurrentPlayer()).toEqual(player2);
  });
});