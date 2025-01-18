import { Board } from "./board";
import { Faction } from "./faction";
import { Game } from "./game";
import { Player, Players } from "./player";
import { Unit } from "./unit";

export class GameCreator {
  createGame(gameData) {
    const board = new Board(gameData.board.rows, gameData.board.columns);
    const game = new Game(gameData.id, ['Movement', 'Combat'], this.#getPlayers(gameData), board);
    this.#addUnits(board, game.getPlayers(), gameData.board);
    return game;
  }

  #getPlayers(gameData) {
    const players = new Array();
    for (let playerData of gameData.players) {
      const player = new Player(playerData.name, playerData.type, this.#getFactions(playerData));
      players.push(player);
    }
    return new Players(players);
  }

  #getFactions(playerData) {
    const factions = new Array();
    for (let faction of playerData.factions) {
      factions.push(new Faction(faction.name, faction.counterColor));
    }
    return factions;
  }

  #addUnits(board, players, boardData) {
    const factionMap = this.#getFactionMap(players);
    for (let unitData of boardData.units) {
      const faction = factionMap.get(unitData.faction.name);
      const unit = new Unit(unitData.name, faction);
      board.addUnit(unit, unitData.row, unitData.column);
    }
  }

  #getFactionMap(players) {
    const factionMap = new Map();
    for (let player of players.getAllPlayers()) {
      for (let faction of player.getFactions()) {
        factionMap.set(faction.getName(), faction);
      }
    }
    return factionMap;
  }
}