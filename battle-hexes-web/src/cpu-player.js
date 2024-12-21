export class CpuPlayer {
  #board;
  #faction;

  constructor(board, faction) {
    this.#board = board;
    this.#faction = faction;  
  }

  movement(drawingCallback) {
    for (let unit of this.#board.getUnits()) {
      console.log(unit);
    }
  }
}