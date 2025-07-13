import axios from 'axios';
import { API_URL } from './model/battle-api.js';

export class Menu {
  #game;
  #selHexContentsDiv;
  #selHexCoordDiv;
  #unitMovesLeftDiv;
  #newGameBtn;
  #gameOverLabel;

  constructor(game) {
    this.#game = game;
    this.#selHexContentsDiv = document.getElementById('selHexContents');
    this.#selHexCoordDiv = document.getElementById('selHexCoord');
    this.#unitMovesLeftDiv = document.getElementById('unitMovesLeftDiv');
    this.#newGameBtn = document.getElementById('newGameBtn');
    this.#gameOverLabel = document.getElementById('gameOverLabel');

    this.#newGameBtn.addEventListener('click', () => location.reload());

    this.#initPhasesInMenu();
    this.#initPhaseEndButton();
    this.#setCurrentTurn();
    this.#updateCombatIndicator();
  }

  #initPhasesInMenu() {
    const phasesElem = document.getElementById('phasesList');

    for (let i = 0; i < this.#game.getPhases().length; i++) {
      const phaseElem = document.createElement('span');
      phaseElem.id = 'phasesList' + this.#game.getPhases()[i];
      
      if (i === 0) {
        phaseElem.classList.add('current-phase');
      }

      phaseElem.textContent = this.#game.getPhases()[i];

      phasesElem.appendChild(phaseElem);

      if (i < this.#game.getPhases().length - 1) {
        const arrow = document.createTextNode(' → ');
        phasesElem.appendChild(arrow);
      }
    }
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
    this.#disableOrEnableActionButton();

    if (this.#game.isGameOver()) {
      this.#showGameOver();
    } else {
      this.#hideGameOver();
    }
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
    if (this.#isCombatPhase()) {
      this.#handleCombatPhase();
    } else {
      this.#finishPhase();
    }
  }

  #isCombatPhase() {
    return this.#game.getCurrentPhase().toLowerCase() === 'combat';
  }

  #handleCombatPhase() {
    console.log('Resolving combat.');
    this.#game.resolveCombat(this.#postCombat).then(() => this.#finishPhase());
  }

  #finishPhase() {
    console.log('Ending phase ' + this.#game.getCurrentPhase() + '.');
    const switchedPlayers = this.#game.endPhase();
    this.updateMenu();
    this.#disableOrEnableActionButton();

    if (switchedPlayers) {
      axios.post(
        `${API_URL}/games/${this.#game.getId()}/end-turn`,
        this.#game.getBoard().sparseBoard()
      ).catch(err => console.error('Failed to update game state', err))
       .finally(() => {
         if (!this.#game.isGameOver()) {
           this.#game.getCurrentPlayer().play(this.#game);
         }
       });
    }
  }

  #disableOrEnableActionButton() {
    const endPhaseBtn = document.getElementById('endPhaseBtn');
    endPhaseBtn.disabled = !this.#game.getCurrentPlayer().isHuman() || this.#game.isGameOver();
  }

  #postCombat() {
    console.log('Combat phase is over.')
    // TODO: update the menu area of the UI to show the results of the combat
  }

  #setCurrentTurn() {
    document.getElementById('currentTurnLabel').innerHTML = this.#game.getCurrentPlayer().getName();
    document.getElementById('endPhaseBtn').textContent = 
        (this.#game.getCurrentPhase().startsWith('End ')? '' : 'End ') + 
            this.#game.getCurrentPhase();
  }

  #updatePhasesStyling() {
    for (let phase of this.#game.getPhases()) {
      const phaseElem = document.getElementById('phasesList' + phase);
      if (phase === this.#game.getCurrentPhase()) {
        phaseElem.classList.add('current-phase');
      } else {
        phaseElem.classList.remove('current-phase');
      }
    }
  }

  #showGameOver() {
    this.#gameOverLabel.style.display = 'block';
    this.#newGameBtn.style.display = 'block';
  }

  #hideGameOver() {
    this.#gameOverLabel.style.display = 'none';
    this.#newGameBtn.style.display = 'none';
  }
}