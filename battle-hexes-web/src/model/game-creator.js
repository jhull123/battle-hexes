import { Board } from "./board";
import { Faction } from "./faction";
import { Game } from "./game";
import { Players } from "../player/player";
import { PlayerFactory } from "../player/player-factory";
import { Unit } from "./unit";
import { Terrain } from "./terrain";

export class GameCreator {
  createGame(gameData) {
    const board = new Board(gameData.board.rows, gameData.board.columns);
    const scenarioId = this.#extractScenarioId(gameData);
    const playerTypeIds = this.#extractPlayerTypeIds(gameData);

    const game = new Game(
      gameData.id,
      ['Movement', 'Combat', 'End Turn'],
      this.#getPlayers(gameData),
      board,
      {
        scenarioId,
        playerTypeIds,
      },
    );
    this.#addTerrain(board, gameData.board);
    this.#addUnits(board, game.getPlayers(), gameData.board);
    return game;
  }

  #extractScenarioId(gameData) {
    const candidates = [
      gameData?.scenarioId,
      gameData?.scenario_id,
    ];

    return candidates.find((value) => typeof value === 'string' && value.trim().length > 0) ?? null;
  }

  #extractPlayerTypeIds(gameData) {
    const candidates = [
      gameData?.playerTypeIds,
      gameData?.playerTypes,
      gameData?.player_type_ids,
      gameData?.player_types,
    ];

    for (const candidate of candidates) {
      if (Array.isArray(candidate) && candidate.every((value) => typeof value === 'string' && value.trim().length > 0)) {
        return [...candidate];
      }
    }

    return null;
  }

  #getPlayers(gameData) {
    const players = new Array();
    const playerFactory = new PlayerFactory();

    for (let playerData of gameData.players) {
      players.push(
        playerFactory.createPlayer(
          playerData.name, playerData.type, this.#getFactions(playerData)));
    }

    return new Players(players);
  }

  #getFactions(playerData) {
    const factions = new Array();
    for (let faction of playerData.factions) {
      factions.push(new Faction(faction.id, faction.name, faction.color));
    }
    return factions;
  }

  #addUnits(board, players, boardData) {
    const factionMap = this.#getFactionMap(players);
    for (let unitData of boardData.units) {
      const faction = factionMap.get(unitData.faction_id);
      const unit = new Unit(
        unitData.id, unitData.name, faction, unitData.type, unitData.attack, 
        unitData.defense, unitData.move);
      board.addUnit(unit, unitData.row, unitData.column);
    }
  }

  #addTerrain(board, boardData) {
    const terrainData = boardData?.terrain;
    const terrainTypes = new Map();

    if (terrainData?.types) {
      for (const [key, value] of Object.entries(terrainData.types)) {
        const name = value?.name ?? key;
        const color = value?.color ?? '#F0F0F0';
        terrainTypes.set(key, new Terrain(name, color));
      }
    }

    const defaultTerrainId = typeof terrainData?.default === 'string' ? terrainData.default : null;
    const defaultTerrain =
      (defaultTerrainId ? terrainTypes.get(defaultTerrainId) : null)
      ?? (defaultTerrainId ? new Terrain(defaultTerrainId, '#F0F0F0') : new Terrain('default', '#F0F0F0'));

    for (const hex of board.getAllHexes()) {
      hex.setTerrain(defaultTerrain);
    }

    if (!Array.isArray(terrainData?.hexes)) {
      return;
    }

    for (const hexData of terrainData.hexes) {
      const targetHex = board.getHex(hexData.row, hexData.column);
      if (!targetHex) {
        continue;
      }
      const terrainId = typeof hexData.terrain === 'string' ? hexData.terrain : null;
      const terrain = terrainId ? terrainTypes.get(terrainId) ?? defaultTerrain : defaultTerrain;
      targetHex.setTerrain(terrain);
    }
  }

  #getFactionMap(players) {
    const factionMap = new Map();
    for (let player of players.getAllPlayers()) {
      for (let faction of player.getFactions()) {
        factionMap.set(faction.getId(), faction);
      }
    }
    return factionMap;
  }
}
