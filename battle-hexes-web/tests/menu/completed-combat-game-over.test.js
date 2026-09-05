/** @jest-environment jsdom */
const completedCombatResponse = {
  units: [],
  activePlayer: null,
  currentPhase: null,
  pendingCombats: [],
  gameStatus: {
    state: 'completed',
    winner: 'Germany',
    message: 'Germany wins by eliminating every Airborne unit.',
  },
  gameLog: [{
    turnNumber: 3,
    playerName: 'Germany',
    events: {
      combat: [{
        attackers: [{ name: 'Grenadiers', attack: 4, defense: 3, movement: 2 }],
        defenders: [{ name: 'Airborne', attack: 3, defense: 4, movement: 2 }],
        baseOdds: [1, 1],
        modifiedOdds: [1, 1],
        defenderTerrain: { name: 'Open', oddsShift: 0 },
        dieRoll: 6,
        result: { code: 'DEFENDER_ELIMINATED', text: 'Defender Eliminated' },
        eliminatedUnits: ['Airborne'],
        retreatedUnits: [],
      }],
      reinforcements: [],
    },
  }],
};

const mockService = {
  listScenarios: jest.fn().mockResolvedValue([]),
  resolveCombat: jest.fn().mockResolvedValue(completedCombatResponse),
  endMovement: jest.fn(),
  endTurn: jest.fn(),
};

jest.mock('../../src/service/service-factory.js', () => ({
  battleHexesService: mockService,
}));
jest.mock('../../src/model/combat-resolver.js', () => ({
  CombatResolver: jest.fn().mockImplementation(() => ({
    resolveCombat: () => Promise.resolve(completedCombatResponse),
  })),
}));

import { Board } from '../../src/model/board.js';
import { Game } from '../../src/model/game.js';
import { Player, Players, playerTypes } from '../../src/player/player.js';
import { Menu } from '../../src/menu.js';
import { GameOverDialog } from '../../src/gameoverdialog.js';
import { GameLogMenu } from '../../src/game-log/game-log-menu.js';

const combatResultsTable = { dieRolls: [], rows: [] };

function buildDom() {
  document.body.innerHTML = `
    <div id="selHexContents"></div><div id="selHexCoord"></div>
    <h4 id="selHexUnitsHeading"></h4><div id="selHexTerrain"></div>
    <h4 id="selHexTerrainHeading"></h4><div id="selHexObjectives"></div>
    <div id="reactionStatus"></div><button id="newGameBtn"></button>
    <div id="gameOverLabel"></div><input type="checkbox" id="autoNewGame">
    <input type="checkbox" id="showHexCoords"><div id="phasesList"></div>
    <button id="endPhaseBtn"></button><div id="currentTurnLabel"></div>
    <div id="victoryTurnLabel"></div><div id="victoryPointsList"></div>
    <div id="reactionMessages"></div><div id="gameLogList"></div>
    <div id="reinforcementsMenu"><div id="reinforcementsList"></div></div>
    <hr id="reinforcementsDivider"><h3 id="scenarioOverviewHeading"></h3>
    <p id="scenarioOverviewDescription"></p><h4 id="scenarioVictoryHeading"></h4>
    <p id="scenarioVictoryDescription"></p>
    <table id="combatResultsTable"></table>
    <div id="gameOverDialog" style="display: none">
      <h2 id="gameOverDialogTitle"></h2><p id="gameOverDialogMessage"></p>
      <button id="gameOverNewGameBtn"></button><button id="gameOverMainMenuBtn"></button>
      <button id="gameOverCloseBtn"></button>
    </div>`;
}

test('completed human combat renders its log and opens the authoritative game-over dialog', async () => {
  buildDom();
  history.replaceState(null, '', '/');
  const players = new Players([
    new Player('Germany', playerTypes.HUMAN, []),
    new Player('Airborne', playerTypes.HUMAN, []),
  ], 'Germany');
  const game = new Game('human-combat', ['Movement', 'Combat', 'End Turn'], players,
    new Board(1, 1), { currentPhase: 'combat', combatResultsTable });
  new GameOverDialog();
  const menu = new Menu(game, { service: mockService });

  menu.doEndPhase();
  await new Promise((resolve) => setTimeout(resolve, 0));

  expect(document.getElementById('endPhaseBtn').textContent).toBe('Game Complete');
  expect(document.getElementById('endPhaseBtn').disabled).toBe(true);
  expect(document.getElementById('gameLogList').textContent)
    .toContain('Combat - Defender Eliminated');
  expect(document.getElementById('gameOverDialog').style.display).toBe('flex');
  expect(document.getElementById('gameOverDialogMessage').textContent)
    .toBe('Germany wins by eliminating every Airborne unit. Winner: Germany');
  expect(mockService.endTurn).not.toHaveBeenCalled();
  expect(mockService.endMovement).not.toHaveBeenCalled();
});

test('opens the game-over dialog before a completed combat log render fails', async () => {
  buildDom();
  history.replaceState(null, '', '/');
  const players = new Players([
    new Player('Germany', playerTypes.HUMAN, []),
    new Player('Airborne', playerTypes.HUMAN, []),
  ], 'Germany');
  const game = new Game('human-combat-render-failure',
    ['Movement', 'Combat', 'End Turn'], players,
    new Board(1, 1), { currentPhase: 'combat', combatResultsTable });
  new GameOverDialog();
  const menu = new Menu(game, { service: mockService });
  const renderError = new Error('combat event could not be rendered');

  await game.resolveCombat();
  jest.spyOn(GameLogMenu.prototype, 'update').mockImplementation(() => {
    throw renderError;
  });

  expect(() => menu.updateMenu()).toThrow(renderError);
  expect(document.getElementById('gameOverDialog').style.display).toBe('flex');
  expect(document.getElementById('gameOverDialogMessage').textContent)
    .toBe('Germany wins by eliminating every Airborne unit. Winner: Germany');
});
