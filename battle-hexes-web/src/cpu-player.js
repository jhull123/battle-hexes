export class CpuPlayer {
  #board;
  #faction;

  constructor(board, faction) {
    this.#board = board;
    this.#faction = faction;  
  }

  movement(drawingCallback, callbackDelay) {
    for (let unit of this.#board.getUnits()) {
      if (unit.getFaction() !== this.#faction) {
        continue;
      }

      while (unit.getMovesRemaining() > 0) {
        let currentHex = unit.getContainingHex();
        let adjHexCoords = [...unit.getContainingHex().getAdjacentHexCoords()];
        let randHexCoords = adjHexCoords[Math.floor(Math.random() * adjHexCoords.length)];
        let randHex = this.#board.getHexStrCoord(randHexCoords);
        this.#board.moveUnit(unit, currentHex, randHex);

        setTimeout(() => {
          drawingCallback([currentHex, randHex]);
        }, callbackDelay);
      }
    }
  }
}