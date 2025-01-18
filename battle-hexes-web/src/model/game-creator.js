import { Board } from "../board";
import { Faction } from "../faction";
import { Game } from "./game";
import { Player, Players } from "./player";

export class GameCreator {
  createGame(gameData) {
    const board = new Board(gameData.board.rows, gameData.board.columns);
    const game = new Game(gameData.id, ['Movement', 'Combat'], this.#getPlayers(gameData), board);
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
}