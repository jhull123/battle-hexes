export class Menu {
  #game;
  #selHexContentsDiv;
  #selHexCoordDiv;
  #unitMovesLeftDiv;

  constructor(game) {
    this.#game = game;
    this.#selHexContentsDiv = document.getElementById('selHexContents');
    this.#selHexCoordDiv = document.getElementById('selHexCoord');
    this.#unitMovesLeftDiv = document.getElementById('unitMovesLeftDiv');

    this.#initPhasesInMenu();
    this.#initPhaseEndButton();
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

  #initPhaseEndButton() {
    document.getElementById('endPhaseBtn').textContent = 'End ' + this.#game.getPhases()[0];
  }

  updateMenu() {
    const selectedHex = this.#game.getBoard().getSelectedHex();

    if (!selectedHex) {
      // nothing here!
    } else if (selectedHex.isEmpty()) {
      this.#selHexContentsDiv.innerHTML = 'Empty Hex';
      this.#selHexCoordDiv.innerHTML = `Hex Coord: (${selectedHex.row}, ${selectedHex.column})`;
    } else {
      this.#selHexContentsDiv.innerHTML = 'Hex contains a unit.';
      this.#selHexCoordDiv.innerHTML = `Hex Coord: (${selectedHex.row}, ${selectedHex.column})`;
    }

    if (this.#game.getBoard().isOwnHexSelected()) {
      // friendly hex selected
      this.#unitMovesLeftDiv.innerHTML = `Moves Left: ${selectedHex.getUnits()[0].getMovesRemaining()}`;
    } else {
      // opposing hex selected
      this.#unitMovesLeftDiv.innerHTML = '';
    }

    this.#updateCombatIndicator();
    this.#setCurrentTurn();
    this.#updatePhasesStyling();
  }

  #updateCombatIndicator() {
    const combatElem = document.getElementById("phasesListCombat");

    if (this.#game.getBoard().hasCombat()) {
      combatElem.classList.remove("disabled-phase");
    } else {
      combatElem.classList.add("disabled-phase");
    }
  }

  doEndPhase() {
    if (this.#game.getCurrentPhase().toLowerCase() === 'combat') {
      console.log('Resolving combat.');
      this.#game.resolveCombat(this.#postCombat);
    } else {
      console.log('Ending phase ' + this.#game.getCurrentPhase() + '.');
      this.#game.endPhase();
      this.updateMenu();
    }
  }

  #postCombat() {
    console.log('Combat phase is over.')
  }

  #setCurrentTurn() {
    document.getElementById('currentTurnLabel').innerHTML = this.#game.getCurrentPlayer().getName();
    document.getElementById('endPhaseBtn').textContent = 'End ' + this.#game.getCurrentPhase();
  }

  #updatePhasesStyling() {
    for (let phase of this.#game.getPhases()) {
      const phaseElem = document.getElementById('phasesList' + phase);
      if (phase === this.#game.getCurrentPhase()) {
        phaseElem.className = 'current-phase';
      } else {
        phaseElem.className = '';
      }
    }
  }
}