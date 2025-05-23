import { Board } from "./board";
import { Faction } from "./faction";
import { Game } from "./game";
import { Players } from "../player/player";
import { PlayerFactory } from "../player/player-factory";
import { Unit } from "./unit";

export class GameCreator {
  createGame(gameData) {
    const board = new Board(gameData.board.rows, gameData.board.columns);
    const game = new Game(
      gameData.id, ['Movement', 'Combat', 'End Turn'], 
      this.#getPlayers(gameData), board);
    this.#addUnits(board, game.getPlayers(), gameData.board);
    return game;
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