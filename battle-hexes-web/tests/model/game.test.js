import { Faction } from "../../src/faction";
import { Game } from "../../src/model/game";

let game;
const phases = ['Movement', 'Combat'];
const players = [new Faction('Red Faction'), new Faction('Blue Faction')];

beforeEach(() => {
  game = new Game(phases, players);
});

describe('constructor', () => {
  test('constructor initializes current phase and player', () => {
    expect(game.getCurrentPhase()).toBe(phases[0]);
    expect(game.getCurrentPlayer()).toEqual(players[0]);
  });
});

describe('endPhase', () => {
  test('endPhase moves to next phase when turn is not over', () => {
    game.endPhase();
    expect(game.getCurrentPhase()).toBe(phases[1]);
    expect(game.getCurrentPlayer()).toEqual(players[0]);
  });

  test('endPhase moves to next player when turn is over', () => {
    game.endPhase();
    game.endPhase();
    expect(game.getCurrentPhase()).toBe(phases[0]);
    expect(game.getCurrentPlayer()).toEqual(players[1]);
  });
});