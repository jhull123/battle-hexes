import { Faction } from "../faction";
import { Game } from "./game";
import { Player } from "./player";

export class GameCreator {
  createGame(gameData) {
    const game = new Game(gameData.id, ['Movement', 'Combat'], this.#getPlayers(gameData));
    return game;
  }

  #getPlayers(gameData) {
    const players = new Array();
    for (let playerData of gameData.players) {
      const player = new Player(playerData.name, playerData.type, this.#getFactions(playerData));
      players.push(player);
    }
    return players;
  }

  #getFactions(playerData) {
    const factions = new Array();
    for (let faction of playerData.factions) {
      factions.push(new Faction(faction.name, faction.counterColor));
    }
    return factions;
  }
}