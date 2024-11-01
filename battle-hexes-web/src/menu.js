export class Menu {
  #board;
  #selHexContentsDiv;
  #selHexCoordDiv;
  #unitMovesLeftDiv;

  constructor(board) {
    this.#board = board;
    this.#selHexContentsDiv = document.getElementById('selHexContents');
    this.#selHexCoordDiv = document.getElementById('selHexCoord');
    this.#unitMovesLeftDiv = document.getElementById('unitMovesLeftDiv');;
  }

  updateMenu() {
    const selectedHex = this.#board.getSelectedHex();

    if (!selectedHex) {
      // nothing here!
    } else if (selectedHex.isEmpty()) {
      this.#selHexContentsDiv.innerHTML = 'Empty Hex';
      this.#selHexCoordDiv.innerHTML = `Hex Coord: (${selectedHex.row}, ${selectedHex.column})`;
    } else {
      this.#selHexContentsDiv.innerHTML = 'Hex contains a unit.';
      this.#selHexCoordDiv.innerHTML = `Hex Coord: (${selectedHex.row}, ${selectedHex.column})`;
    }

    if (this.#board.ownHexSelected()) {
      // friendly hex selected
      this.#unitMovesLeftDiv.innerHTML = `Moves Left: ${selectedHex.getUnits()[0].getMovesRemaining()}`;
    } else {
      // opposing hex selected
      this.#unitMovesLeftDiv.innerHTML = '';
    }
  }

  doEndTurn() {
    const currentFaction = this.#board.endTurn();
    this.setCurrentTurn(currentFaction);
    this.updateMenu();
  }

  setCurrentTurn(faction) {
    document.getElementById('currentTurnLabel').innerHTML = faction.getName()
  }
}