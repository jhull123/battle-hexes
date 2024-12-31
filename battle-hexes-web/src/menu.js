export class Menu {
  #game;
  #board;
  #selHexContentsDiv;
  #selHexCoordDiv;
  #unitMovesLeftDiv;

  constructor(game, board) {
    this.#game = game;
    this.#board = board;
    this.#selHexContentsDiv = document.getElementById('selHexContents');
    this.#selHexCoordDiv = document.getElementById('selHexCoord');
    this.#unitMovesLeftDiv = document.getElementById('unitMovesLeftDiv');
    this.#initPhasesInMenu();    
  }

  #initPhasesInMenu() {
    const phasesElem = document.getElementById('phasesList');

    for (let i = 0; i < this.#game.getPhases().length; i++) {
      const phaseElem = document.createElement('span');
      phaseElem.id = 'phasesList' + this.#game.getPhases()[i];
      phaseElem.className = i === 0 ? 'current-phase' : 'disabled-phase';
      phaseElem.textContent = this.#game.getPhases()[i];

      phasesElem.appendChild(phaseElem);

      const arrow = document.createTextNode(' → ');
      phasesElem.appendChild(arrow);
    }

    const endTurnPhase = document.createElement('span');
    endTurnPhase.textContent = 'End Turn';
    phasesElem.appendChild(endTurnPhase);
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

    if (this.#board.isOwnHexSelected()) {
      // friendly hex selected
      this.#unitMovesLeftDiv.innerHTML = `Moves Left: ${selectedHex.getUnits()[0].getMovesRemaining()}`;
    } else {
      // opposing hex selected
      this.#unitMovesLeftDiv.innerHTML = '';
    }

    this.updateCombatIndicator();
  }

  updateCombatIndicator() {
    const combatElem = document.getElementById("phasesListCombat");

    if (this.#board.hasCombat()) {
      combatElem.classList.remove("disabled-phase");
    } else {
      combatElem.classList.add("disabled-phase");
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