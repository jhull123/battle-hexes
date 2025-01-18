import { GameCreator } from "../../src/model/game-creator";
import { Hex } from "../../src/model/hex";

let game;

beforeEach(() => {
  const gameCreator = new GameCreator();
  const gameData = JSON.parse(
    '{"id":"093e432e-28ba-4dd1-a202-0802ee6ef32b","players":[{"name":"Player 1","type":"Human","factions":[{"name":"Red Faction","color":"#C81010"}]},{"name":"Player 2","type":"Computer","factions":[{"name":"Blue Faction","color":"#4682B4"}]}],' +
    '"board":{"rows":10,"columns":10,"units":[' +
    '{"name":"Red Unit","row":6,"column":4,"faction":{"name":"Red Faction","color":"#C81010"}},' +
    '{"name":"Blue Unit","row":3,"column":5,"faction":{"name":"Blue Faction","color":"#4682B4"}}]}}'
  );
  game = gameCreator.createGame(gameData);
});

describe("createGame", () => {
  test("create game sets game id", () => {
    expect(game.getId()).toBe("093e432e-28ba-4dd1-a202-0802ee6ef32b");
  });

  test("create game sets players", () => {
    const allPlayers = game.getPlayers().getAllPlayers();

    expect(allPlayers.length).toBe(2);
    expect(allPlayers[0].getName()).toBe("Player 1");
    expect(allPlayers[1].getName()).toBe("Player 2");
    expect(allPlayers[0].getType()).toBe("Human");
    expect(allPlayers[1].getType()).toBe("Computer");
    expect(allPlayers[0].getFactions().length).toBe(1);
    expect(allPlayers[1].getFactions().length).toBe(1);
    expect(allPlayers[0].getFactions()[0].getName()).toBe("Red Faction");
    expect(allPlayers[1].getFactions()[0].getName()).toBe("Blue Faction");
  });

  test("create game sets phases", () => {
    expect(game.getPhases().length).toBe(2);
    expect(game.getPhases()[0]).toBe("Movement");
    expect(game.getPhases()[1]).toBe("Combat");
  });

  test("board size is set", () => {
    expect(game.getBoard().getHex(9, 9)).toBeInstanceOf(Hex); 
  });

  test("board has two units", () => {
    expect(game.getBoard().getUnits().size).toBe(2)
  });

  test("board has units in correct hexes", () => {
    const unit1 = game.getBoard().getHex(6, 4).getUnits().values().next().value;
    const unit2 = game.getBoard().getHex(3, 5).getUnits().values().next().value;

    expect(unit1.getName()).toBe("Red Unit");
    expect(unit2.getName()).toBe("Blue Unit");
  });
});