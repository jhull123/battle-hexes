import axios from 'axios';
import { API_URL } from './model/battle-api.js';
import { eventBus } from './event-bus.js';

export class Menu {
  #game;
  #selHexContentsDiv;
  #selHexCoordDiv;
  #unitMovesLeftDiv;
  #newGameBtn;
  #gameOverLabel;
  #autoNewGameChk;
  #showHexCoordsChk;
  #autoReloadScheduled = false;
  static #SHOW_HEX_COORDS_STORAGE_KEY = 'battleHexes.showHexCoords';

  constructor(game) {
    this.#game = game;
    this.#selHexContentsDiv = document.getElementById('selHexContents');
    this.#selHexCoordDiv = document.getElementById('selHexCoord');
    this.#unitMovesLeftDiv = document.getElementById('unitMovesLeftDiv');
    this.#newGameBtn = document.getElementById('newGameBtn');
    this.#gameOverLabel = document.getElementById('gameOverLabel');
    this.#autoNewGameChk = document.getElementById('autoNewGame');
    this.#showHexCoordsChk = document.getElementById('showHexCoords');

    // Initialize checkbox state from URL param
    const params = new URLSearchParams(window.location.search);
    this.#autoNewGameChk.checked = params.get('autoNewGame') === '1';

    this.#newGameBtn.addEventListener('click', () => location.reload());
    this.#autoNewGameChk.addEventListener('change', () => {
      const params = new URLSearchParams(window.location.search);
      if (this.#autoNewGameChk.checked) {
        params.set('autoNewGame', '1');
      } else {
        params.delete('autoNewGame');
      }
      const qs = params.toString();
      const canReplace =
          window.location.protocol === 'http:' || window.location.protocol === 'https:';

      if (canReplace) {
        history.replaceState(null, '', qs ? `${location.pathname}?${qs}` : location.pathname);
      }
      
      if (this.#game.isGameOver()) {
        this.#showGameOver();
      }
    });

    const storedShowCoords = this.#getStoredShowHexCoords();
    this.#showHexCoordsChk.checked = storedShowCoords ?? true;
    this.#showHexCoordsChk.addEventListener('change', () => {
      const shouldShowCoords = this.#showHexCoordsChk.checked;
      this.#storeShowHexCoords(shouldShowCoords);
      eventBus.emit('hexCoordsVisibilityChanged', shouldShowCoords);
    });
    this.#storeShowHexCoords(this.#showHexCoordsChk.checked);
    eventBus.emit('hexCoordsVisibilityChanged', this.#showHexCoordsChk.checked);

    this.#initPhasesInMenu();
    this.#initPhaseEndButton();
    this.#setCurrentTurn();
    this.#updateCombatIndicator();
  }

  getShowHexCoordsPreference() {
    return this.#showHexCoordsChk.checked;
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

  #getStoredShowHexCoords() {
    try {
      const storedValue = window.localStorage?.getItem(Menu.#SHOW_HEX_COORDS_STORAGE_KEY);
      if (storedValue === null || storedValue === undefined) {
        return null;
      }
      return storedValue === 'true';
    } catch (err) {
      console.warn('Failed to read showHexCoords preference from localStorage', err);
      return null;
    }
  }

  #storeShowHexCoords(shouldShow) {
    try {
      window.localStorage?.setItem(Menu.#SHOW_HEX_COORDS_STORAGE_KEY, shouldShow ? 'true' : 'false');
    } catch (err) {
      console.warn('Failed to persist showHexCoords preference to localStorage', err);
    }
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
    if (this.#autoNewGameChk.checked) {
      this.#newGameBtn.style.display = 'none';
      if (!this.#autoReloadScheduled) {
        this.#autoReloadScheduled = true;
        setTimeout(() => location.reload(), 2000);
      }
    } else {
      this.#newGameBtn.style.display = 'block';
    }
  }

  #hideGameOver() {
    this.#gameOverLabel.style.display = 'none';
    this.#newGameBtn.style.display = 'none';
  }
}