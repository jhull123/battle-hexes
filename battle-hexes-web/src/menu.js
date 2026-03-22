import axios from 'axios';
import { API_URL } from './model/battle-api.js';
import { eventBus } from './event-bus.js';

export class Menu {
  #game;
  #selHexContentsDiv;
  #selHexCoordDiv;
  #selHexTerrainDiv;
  #selHexUnitsHeading;
  #selHexTerrainHeading;
  #selHexObjectivesDiv;
  #reactionStatusDiv;
  #newGameBtn;
  #gameOverLabel;
  #autoNewGameChk;
  #showHexCoordsChk;
  #victoryPointsList;
  #scenarioOverviewHeading;
  #scenarioOverviewDescription;
  #scenarioVictoryHeading;
  #scenarioVictoryDescription;
  #activeScenarioId;
  #scenarioDetailsRequestId = 0;
  #autoReloadScheduled = false;
  #onNewGameRequested;
  static #SHOW_HEX_COORDS_STORAGE_KEY = 'battleHexes.showHexCoords';
  static #DEFAULT_SWATCH_COLOR = '#B0B0B0';

  constructor(game, { onNewGameRequested } = {}) {
    this.#game = game;
    this.#selHexContentsDiv = document.getElementById('selHexContents');
    this.#selHexCoordDiv = document.getElementById('selHexCoord');
    this.#selHexTerrainDiv = document.getElementById('selHexTerrain');
    this.#selHexUnitsHeading = document.getElementById('selHexUnitsHeading');
    this.#selHexTerrainHeading = document.getElementById('selHexTerrainHeading');
    this.#selHexObjectivesDiv = document.getElementById('selHexObjectives');
    this.#reactionStatusDiv = document.getElementById('reactionStatus');
    this.#newGameBtn = document.getElementById('newGameBtn');
    this.#gameOverLabel = document.getElementById('gameOverLabel');
    this.#autoNewGameChk = document.getElementById('autoNewGame');
    this.#showHexCoordsChk = document.getElementById('showHexCoords');
    this.#victoryPointsList = document.getElementById('victoryPointsList');
    this.#scenarioOverviewHeading = document.getElementById('scenarioOverviewHeading');
    this.#scenarioOverviewDescription = document.getElementById('scenarioOverviewDescription');
    this.#scenarioVictoryHeading = document.getElementById('scenarioVictoryHeading');
    this.#scenarioVictoryDescription = document.getElementById('scenarioVictoryDescription');
    this.#activeScenarioId = this.#game.getScenarioId?.() ?? null;
    this.#onNewGameRequested = onNewGameRequested;

    // Initialize checkbox state from URL param
    const params = new URLSearchParams(window.location.search);
    this.#autoNewGameChk.checked = params.get('autoNewGame') === '1';

    this.#newGameBtn.addEventListener('click', () => this.#handleNewGameRequest());
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
    eventBus.on('defensiveFireResolved', (events) => {
      this.#showDefensiveFireStatus(events);
    });

    this.#initPhasesInMenu();
    this.#initPhaseEndButton();
    this.#renderScenarioOverview();
    this.#loadScenarioDetails(this.#activeScenarioId);
    this.#setCurrentTurn();
    this.#updateCombatIndicator();
    this.updateMenu();
  }

  #renderScenarioOverview(scenario = null) {
    if (!this.#scenarioOverviewHeading || !this.#scenarioVictoryHeading) {
      return;
    }

    const fallbackScenarioId = this.#activeScenarioId ?? this.#game.getScenarioId?.() ?? '';
    const scenarioHeading = scenario?.name || scenario?.id || fallbackScenarioId;
    this.#scenarioOverviewHeading.textContent = scenarioHeading || 'Scenario';

    if (this.#scenarioOverviewDescription) {
      this.#scenarioOverviewDescription.textContent = scenario?.description || '';
      this.#scenarioOverviewDescription.style.display = this.#scenarioOverviewDescription.textContent ? '' : 'none';
    }

    if (this.#scenarioVictoryDescription) {
      const victoryDescription = scenario?.victory?.description || '';
      this.#scenarioVictoryDescription.textContent = victoryDescription;
      this.#scenarioVictoryHeading.style.display = victoryDescription ? '' : 'none';
      this.#scenarioVictoryDescription.style.display = victoryDescription ? '' : 'none';
    }
  }

  #loadScenarioDetails(scenarioId) {
    if (!scenarioId) {
      this.#renderScenarioOverview();
      return;
    }

    const requestId = this.#scenarioDetailsRequestId + 1;
    this.#scenarioDetailsRequestId = requestId;
    axios.get(`${API_URL}/scenarios`)
      .then((response) => {
        if (requestId !== this.#scenarioDetailsRequestId) {
          return;
        }
        const scenarios = Array.isArray(response?.data) ? response.data : [];
        const scenario = scenarios.find((value) => value?.id === scenarioId);
        this.#renderScenarioOverview(scenario);
      })
      .catch((error) => {
        if (requestId !== this.#scenarioDetailsRequestId) {
          return;
        }
        console.warn('Failed to load scenario details for menu', error);
        this.#renderScenarioOverview();
      });
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
      this.#selHexContentsDiv.innerHTML = '';
      this.#selHexCoordDiv.innerHTML = '<em>No selection</em>';
      this.#selHexTerrainDiv.innerHTML = '';
      this.#selHexObjectivesDiv.innerHTML = '';
      this.#toggleSelectedHexHeadings(false);
    } else {
      this.#selHexCoordDiv.innerHTML = `Coords: (${selectedHex.row}, ${selectedHex.column})`;
      this.#selHexContentsDiv.innerHTML = this.#formatSelectedHexUnits(selectedHex);
      this.#toggleSelectedHexHeadings(true);
    }

    if (selectedHex) {
      const terrain = selectedHex.getTerrain();
      this.#selHexTerrainDiv.innerHTML = this.#formatSelectedHexTerrain(terrain);
      this.#selHexObjectivesDiv.innerHTML = this.#formatObjectives(selectedHex);
    }

    this.#updateCombatIndicator();
    this.#setCurrentTurn();
    this.#updateVictoryPoints();
    this.#updatePhasesStyling();
    this.#disableOrEnableActionButton();

    if (this.#game.isGameOver()) {
      this.#showGameOver();
    } else {
      this.#hideGameOver();
    }
  }

  #toggleSelectedHexHeadings(isVisible) {
    const displayValue = isVisible ? '' : 'none';
    if (this.#selHexUnitsHeading) {
      this.#selHexUnitsHeading.style.display = displayValue;
    }
    if (this.#selHexTerrainHeading) {
      this.#selHexTerrainHeading.style.display = displayValue;
    }
  }

  #showDefensiveFireStatus(events) {
    if (!this.#reactionStatusDiv) {
      return;
    }

    const eventMessages = Array.isArray(events)
      ? events
        .map((event) => event?.message)
        .filter((message) => typeof message === 'string' && message.length > 0)
      : [];

    this.#reactionStatusDiv.textContent = eventMessages.join(' ');
  }

  #formatSelectedHexUnits(selectedHex) {
    const units = selectedHex?.getUnits?.() ?? [];
    if (units.length === 0) {
      return '<em>None</em>';
    }

    return units
      .map((unit) => {
        const echelon = unit.getEchelon?.();
        const unitStrength = `${unit.getAttack()}-${unit.getDefense()}-${unit.getMovement()}`;
        const movesRemaining = unit.getMovesRemaining?.();
        const movesDisplay = Number.isFinite(movesRemaining) ? movesRemaining : 0;
        const color = this.#getPlayerSwatchColor(unit.getOwningPlayer?.());
        const tooltipText = echelon
          ? `${echelon}, ${unitStrength}`
          : unitStrength;
        return `<div class="selected-unit-row"><span class="victory-swatch selected-unit-swatch" style="background-color: ${color};"></span><span class="selected-unit-label" title="${tooltipText}">${unit.getName()} <span class="selected-unit-moves">(moves ${movesDisplay})</span></span></div>`;
      })
      .join('');
  }

  #formatSelectedHexTerrain(terrain) {
    if (!terrain) {
      return '';
    }

    const moveCost = Number.isFinite(terrain.moveCost) && terrain.moveCost > 0
      ? terrain.moveCost
      : 1;
    const terrainName = terrain.name
      ? `${terrain.name.charAt(0).toUpperCase()}${terrain.name.slice(1)}`
      : 'Unknown';
    return `${terrainName} (cost=${moveCost})`;
  }

  #formatObjectives(selectedHex) {
    if (!selectedHex?.hasObjectives?.() || selectedHex.getObjectives().length === 0) {
      return '';
    }

    return selectedHex.getObjectives()
      .map((objective) => {
        const points = objective.points;
        const pointsLabel = points === 1 ? 'pt/turn' : 'pts/turn';
        return `🚩 ${objective.displayName} (${points} ${pointsLabel})`;
      })
      .join('<br/>');
  }

  #updateVictoryPoints() {
    const turnLabel = document.getElementById('victoryTurnLabel');
    if (turnLabel) {
      const turnNumber = this.#game.getTurnNumber?.() ?? 1;
      const turnLimit = this.#game.getTurnLimit?.();
      const limitedTurnNumber = Number.isInteger(turnLimit) && turnLimit > 0
        ? Math.min(turnNumber, turnLimit)
        : turnNumber;
      const turnLimitDisplay = Number.isInteger(turnLimit) && turnLimit > 0 ? turnLimit : '∞';
      turnLabel.textContent = `Turn ${limitedTurnNumber} / ${turnLimitDisplay}`;
    }

    if (!this.#victoryPointsList) {
      return;
    }

    this.#victoryPointsList.innerHTML = '';
    const players = this.#game.getPlayers()?.getAllPlayers?.() ?? [];
    const scores = this.#game.getScores?.() ?? {};
    const currentPlayerName = this.#game.getCurrentPlayer?.()?.getName?.();

    for (const player of players) {
      const row = document.createElement('div');
      row.classList.add('victory-row');

      const swatch = document.createElement('span');
      swatch.classList.add('victory-swatch');
      swatch.style.backgroundColor = this.#getPlayerSwatchColor(player);

      const name = document.createElement('span');
      const playerName = player.getName?.() ?? 'Unknown';
      name.classList.add('victory-name');
      name.textContent = playerName;

      const isCurrentPlayer = typeof currentPlayerName === 'string'
        && currentPlayerName === playerName;
      if (isCurrentPlayer) {
        row.classList.add('victory-row-current');
      }

      const turnBadge = isCurrentPlayer
        ? document.createElement('span')
        : null;
      if (turnBadge) {
        turnBadge.classList.add('victory-turn-badge');
        turnBadge.textContent = 'Turn';
      }

      const leader = document.createElement('span');
      leader.classList.add('victory-leader');

      const score = document.createElement('span');
      score.classList.add('victory-score');
      const value = scores[playerName];
      score.textContent = Number.isFinite(value) ? value : 0;

      row.append(swatch, name, ...(turnBadge ? [turnBadge] : []), leader, score);
      this.#victoryPointsList.appendChild(row);
    }
  }

  #getPlayerSwatchColor(player) {
    const factions = player?.getFactions?.() ?? [];
    if (Array.isArray(factions) && factions.length > 0) {
      const color = factions[0]?.getCounterColor?.();
      if (typeof color === 'string' && color.trim().length > 0) {
        return color;
      }
    }
    return Menu.#DEFAULT_SWATCH_COLOR;
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

    const endTurnPayload = this.#game.getCurrentPhase().toLowerCase() === 'end turn'
      ? this.#game.getBoard().sparseBoard()
      : null;

    if (this.#game.getCurrentPhase().toLowerCase() === 'movement') {
      axios.post(
        `${API_URL}/games/${this.#game.getId()}/end-movement`,
        this.#game.getBoard().sparseBoard()
      ).then((response) => {
        this.#game.updateScores?.(response?.data?.scores);
        this.#game.updateTurnState?.({
          turnLimit: response?.data?.turnLimit,
          turnNumber: response?.data?.turnNumber,
        });
        this.updateMenu();
      }).catch(err => console.error('Failed to update movement state', err));
    }
    const switchedPlayers = this.#game.endPhase();
    this.updateMenu();
    eventBus.emit('redraw');
    this.#disableOrEnableActionButton();

    if (switchedPlayers) {
      axios.post(
        `${API_URL}/games/${this.#game.getId()}/end-turn`,
        endTurnPayload
      ).then((response) => {
        this.#game.updateScores?.(response?.data?.scores);
        this.#game.updateTurnState?.({
          turnLimit: response?.data?.turnLimit,
          turnNumber: response?.data?.turnNumber,
        });
        this.updateMenu();
      }).catch(err => console.error('Failed to update game state', err))
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
      this.#scheduleAutoNewGame();
    } else {
      this.#newGameBtn.style.display = 'block';
    }
  }

  #hideGameOver() {
    this.#gameOverLabel.style.display = 'none';
    this.#newGameBtn.style.display = 'none';
  }

  setGame(game) {
    this.#game = game;
    const scenarioId = this.#game.getScenarioId?.() ?? null;
    if (scenarioId !== this.#activeScenarioId) {
      this.#activeScenarioId = scenarioId;
      this.#renderScenarioOverview();
      this.#loadScenarioDetails(this.#activeScenarioId);
    }
    this.#autoReloadScheduled = false;
    this.#hideGameOver();
    this.updateMenu();
  }

  #handleNewGameRequest() {
    if (!this.#onNewGameRequested) {
      return;
    }

    this.#autoReloadScheduled = false;
    this.#newGameBtn.disabled = true;

    Promise.resolve(this.#onNewGameRequested())
      .catch((err) => {
        console.error('Failed to start new game', err);
        if (this.#autoNewGameChk.checked) {
          this.#scheduleAutoNewGame();
        }
      })
      .finally(() => {
        this.#newGameBtn.disabled = false;
      });
  }

  #scheduleAutoNewGame() {
    if (this.#autoReloadScheduled) {
      return;
    }

    this.#autoReloadScheduled = true;
    setTimeout(() => {
      this.#autoReloadScheduled = false;
      this.#handleNewGameRequest();
    }, 2000);
  }
}
