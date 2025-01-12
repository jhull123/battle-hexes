import { GameCreator } from "../../src/model/game-creator";

let gameCreator;
let gameData;

beforeEach(() => {
  gameCreator = new GameCreator();
  gameData = JSON.parse(
    '{"id":"093e432e-28ba-4dd1-a202-0802ee6ef32b","players":[{"name":"Player 1","type":"Human","factions":[{"name":"Red Faction","color":"#C81010"}]},{"name":"Player 2","type":"Computer","factions":[{"name":"Blue Faction","color":"#4682B4"}]}],"board":{"rows":10,"columns":10,"units":[{"row":6,"column":4,"faction":{"name":"Red Faction","color":"#C81010"}},{"row":3,"column":5,"faction":{"name":"Blue Faction","color":"#4682B4"}}]}}'
  );
});

describe("createGame", () => {
  test("create game sets game id", () => {
    const game = gameCreator.createGame(gameData);
    expect(game.getId()).toBe("093e432e-28ba-4dd1-a202-0802ee6ef32b");
  });
});