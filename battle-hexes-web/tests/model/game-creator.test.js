import { GameCreator } from "../../src/model/game-creator";
import { Hex } from "../../src/model/hex";

let game;

beforeEach(() => {
  const gameCreator = new GameCreator();
  const gameData = JSON.parse(
    '{"id":"093e432e-28ba-4dd1-a202-0802ee6ef32b",' +
    '"scenarioId":"elem_test",' +
    '"playerTypeIds":["human","q-learning"],' +
    '"players":[{"name":"Player 1","type":"Human","factions":[{"id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","name":"Red Faction","color":"#C81010"}]},' +
    '{"name":"Player 2","type":"Computer","factions":[{"id":"38400000-8cf0-41bd-b23e-10b96e4ef00d","name":"Blue Faction","color":"#4682B4"}]}],' +
    '"board":{"rows":10,"columns":10,"units":[' +
    '{"id":"a22c90d0-db87-41d0-8c3a-00c04fd708be","name":"Red Unit","faction_id":"f47ac10b-58cc-4372-a567-0e02b2c3d479","type":"Infantry","attack":2,"defense":2,"move":6,"row":6,"column":4},' +
    '{"id":"c9a440d2-2b0a-4730-b4c6-da394b642c61","name":"Blue Unit","faction_id":"38400000-8cf0-41bd-b23e-10b96e4ef00d","type":"Infantry","attack":4,"defense":4,"move":4,"row":3,"column":5}],' +
    '"terrain":{"default":"open","types":{"open":{"name":"open","color":"#C6AA5C"},"village":{"name":"village","color":"#9A8F7A"}},"hexes":[{"row":6,"column":4,"terrain":"village"}]},' +
    '"road_types":{"secondary":1.0},' +
    '"road_paths":[{"type":"secondary","path":[{"row":5,"column":0},{"row":5,"column":1},{"row":6,"column":2}]}]},' +
    '"objectives":[{"row":6,"column":4,"points":3,"type":"hold"}]}'
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

    expect(allPlayers[0].getFactions()[0].getCounterColor()).toBe("#C81010");
    expect(allPlayers[1].getFactions()[0].getCounterColor()).toBe("#4682B4");
  });

  test("create game sets phases", () => {
    expect(game.getPhases().length).toBe(3);
    expect(game.getPhases()[0]).toBe("Movement");
    expect(game.getPhases()[1]).toBe("Combat");
    expect(game.getPhases()[2]).toBe("End Turn");
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

  test("board has units with correct stats", () => {
    const unit1 = game.getBoard().getHex(6, 4).getUnits().values().next().value;
    const unit2 = game.getBoard().getHex(3, 5).getUnits().values().next().value;

    expect(unit1.getType()).toBe("Infantry");
    expect(unit1.getAttack()).toBe(2);
    expect(unit1.getDefense()).toBe(2);
    expect(unit1.getMovement()).toBe(6);

    expect(unit2.getType()).toBe("Infantry");
    expect(unit2.getAttack()).toBe(4);
    expect(unit2.getDefense()).toBe(4);
    expect(unit2.getMovement()).toBe(4);
  });

  test('game exposes configuration metadata from payload', () => {
    expect(game.getScenarioId()).toBe('elem_test');
    expect(game.getPlayerTypeIds()).toEqual(['human', 'q-learning']);
  });

  test('creates fallback default terrain when none specified', () => {
    const gameCreator = new GameCreator();
    const gameData = {
      id: 'terrain-default',
      players: [
        { name: 'Player 1', type: 'Human', factions: [{ id: 'red', name: 'Red', color: '#C81010' }] },
        { name: 'Player 2', type: 'Computer', factions: [{ id: 'blue', name: 'Blue', color: '#4682B4' }] },
      ],
      board: {
        rows: 1,
        columns: 1,
        units: [],
        terrain: {
          types: {
            open: { name: 'open', color: '#C6AA5C' },
          },
          hexes: [],
        },
      },
    };

    const terrainGame = gameCreator.createGame(gameData);
    const terrainHex = terrainGame.getBoard().getHex(0, 0);

    expect(terrainHex.getTerrain().name).toBe('default');
    expect(terrainHex.getTerrain().color).toBe('#F0F0F0');
  });

  test('board assigns default terrain to unspecified hexes', () => {
    const defaultHex = game.getBoard().getHex(0, 0);

    expect(defaultHex.getTerrain().name).toBe('open');
    expect(defaultHex.getTerrain().color).toBe('#C6AA5C');
  });

  test('board assigns terrain overrides to specified hexes', () => {
    const terrainHex = game.getBoard().getHex(6, 4);

    expect(terrainHex.getTerrain().name).toBe('village');
    expect(terrainHex.getTerrain().color).toBe('#9A8F7A');
  });

  test('board assigns objectives to specified hexes', () => {
    const objectiveHex = game.getBoard().getHex(6, 4);
    const objective = objectiveHex.getObjectives()[0];

    expect(objective.type).toBe('hold');
    expect(objective.points).toBe(3);
  });

  test('board loads roads from board payload', () => {
    const roads = game.getBoard().getRoads();

    expect(roads).toHaveLength(1);
    expect(roads[0].type).toBe('secondary');
    expect(roads[0].movementCost).toBe(1.0);
    expect(roads[0].path).toEqual([[5, 0], [5, 1], [6, 2]]);
  });

  test('board still loads roads from top-level game payload', () => {
    const gameCreator = new GameCreator();
    const gameData = {
      id: 'legacy-roads',
      players: [
        { name: 'Player 1', type: 'Human', factions: [{ id: 'red', name: 'Red', color: '#C81010' }] },
        { name: 'Player 2', type: 'Computer', factions: [{ id: 'blue', name: 'Blue', color: '#4682B4' }] },
      ],
      board: {
        rows: 2,
        columns: 2,
        units: [],
      },
      road_types: { secondary: 1.0 },
      road_paths: [{ type: 'secondary', path: [{ row: 0, column: 0 }, { row: 0, column: 1 }] }],
    };

    const legacyRoadGame = gameCreator.createGame(gameData);
    const roads = legacyRoadGame.getBoard().getRoads();

    expect(roads).toHaveLength(1);
    expect(roads[0].path).toEqual([[0, 0], [0, 1]]);
  });
});
