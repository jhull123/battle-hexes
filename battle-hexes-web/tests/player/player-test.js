import { Player } from "../../src/player/player";
import { Players } from "../../src/player/player";

let player1;
let player2;
let players;

beforeEach(() => {
  player1 = new Player("Player 1");
  player2 = new Player("Player 2");
  players = new Players([player1, player2]);
});

describe("Players", () => {
  test("get current player", () => {
    expect(players.getCurrentPlayer()).toBe(player1);
  });

  test("next player", () => {
    expect(players.nextPlayer()).toBe(player2);
    expect(players.nextPlayer()).toBe(player1);
  });
});