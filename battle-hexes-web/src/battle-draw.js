import p5 from 'p5';
import { eventBus } from './event-bus.js';
import { Game } from './model/game.js';
import { HexDrawer } from './drawer/hex-drawer.js';
import { UnitDrawer } from './drawer/unit-drawer.js';
import { SelectionDrawer } from './drawer/selection-drawer.js';
import { MoveSelectionDrawer } from './drawer/selection-drawer.js';
import { CombatSelectionDrawer } from './drawer/selection-drawer.js';
import { MoveArrowDrawer } from './drawer/move-arrow-drawer.js';
import { RoadDrawer } from './drawer/road-drawer.js';
import { TerrainOverlayDrawer } from './drawer/terrain-overlay-drawer.js';
import { Menu } from './menu.js';
import './styles/menu.css';
import { GameCreator } from './model/game-creator.js';
import {
  getLastLoadedConfig,
  loadGameData,
  rememberLoadedGameData,
  updateUrlWithGameId,
} from './model/game-loader.js';

const gameData = await loadGameData();
console.log('game data: ' + JSON.stringify(gameData));

new p5((p) => {
  const hexRadius = 50;
  const hexHeight = Math.sqrt(3) * hexRadius;
  const hexDiameter = hexRadius * 2;
  const menuWidth = 300;
  const hexRows = 10;
  const canvasMargin = 20;
  
  let game = new GameCreator().createGame(gameData);
  let menu;

  const createNewGameAndLoad = async () => {
    const cachedConfig = getLastLoadedConfig();
    const scenarioId = game.getScenarioId() ?? cachedConfig.scenarioId;
    const playerTypes = game.getPlayerTypeIds() ?? cachedConfig.playerTypes;
    const newGameData = await Game.newGameFromServer({
      scenarioId,
      playerTypes,
    });
    updateUrlWithGameId(newGameData.id);
    rememberLoadedGameData(newGameData);
    game = new GameCreator().createGame(newGameData);
    menu.setGame(game);

    if (!game.getCurrentPlayer().isHuman()) {
      game.getCurrentPlayer().play(game);
    }

    hexDrawWithCoords.setShowHexCoords(menu.getShowHexCoordsPreference());
    eventBus.emit('menuUpdate');
    eventBus.emit('redraw');
  };

  menu = new Menu(game, { onNewGameRequested: createNewGameAndLoad });

  if (!game.getCurrentPlayer().isHuman()) {
    game.getCurrentPlayer().play(game);
  }

  const hexDrawWithCoords = new HexDrawer(p, hexRadius);
  hexDrawWithCoords.setShowHexCoords(menu.getShowHexCoordsPreference());
  const hexDraw = new HexDrawer(p, hexRadius);
  const roadDraw = new RoadDrawer(p, hexDraw, () => game.getBoard().getRoads());
  const terrainOverlayDraw = new TerrainOverlayDrawer(p, hexDraw);
  
  const unitDraw = new UnitDrawer(p, hexDraw);
  const combatSelectionDraw = new CombatSelectionDrawer(new HexDrawer(p, hexRadius));
  const selectionDraw = new SelectionDrawer(hexDraw);
  const moveSelectionDraw = new MoveSelectionDrawer(hexDraw);
  const moveArrowDraw = new MoveArrowDrawer(p, hexDraw);
  const drawers = [
    hexDrawWithCoords,
    roadDraw,
    terrainOverlayDraw,
    combatSelectionDraw,
    selectionDraw,
    moveSelectionDraw,
    unitDraw,
    moveArrowDraw,
  ];

  eventBus.on('hexCoordsVisibilityChanged', (shouldShow) => {
    hexDrawWithCoords.setShowHexCoords(shouldShow);
    p.draw();
  });

  let canvas;

  p.setup = function() {
    console.log("Let's set it up!");
    document.getElementById('endPhaseBtn').addEventListener('click', menu.doEndPhase.bind(menu));
    canvas = p.createCanvas(getCanvasWidth(), getCanvasHeight());
    canvas.parent('canvas-container');
    p.noLoop();

    eventBus.on('redraw', () => {
      console.log('Redrawing board.');
      p.draw();
    });
    eventBus.on('menuUpdate', () => {
      menu.updateMenu();
    });
  };

  p.draw = function() {
    // console.log("I'm starting to draw!");
    p.background(90);
  
    for (let drawer of drawers) {
      if (typeof drawer.drawAll === 'function') {
        drawer.drawAll();
        continue;
      }

      for (let currentHex of game.getBoard().getAllHexes()) {
        drawer.draw(currentHex);
      }
    }  
  };

  p.windowResized = function() {
    p.resizeCanvas(getCanvasWidth(), getCanvasHeight());
  }

  p.mousePressed = function() {
    const canvasBounds = canvas.elt.getBoundingClientRect();
    if (p.mouseX > canvasBounds.right - 10) {
      // non-canvas click
      return;
    }

    let clickedHexPos = pixelToHex(p.mouseX, p.mouseY);
    console.log("Clicked on hex:", clickedHexPos.row, clickedHexPos.col);

    let clickedHex = game.getBoard().getHex(clickedHexPos.row, clickedHexPos.col);
    let prevSelectedHex = game.getBoard().selectHex(clickedHex);

    drawHexNeighborhood([prevSelectedHex, clickedHex]);

    menu.updateMenu();
  }

  p.mouseMoved = function() {
    let mouseHexPos = pixelToHex(p.mouseX, p.mouseY);
    let hoverHex = game.getBoard().getHex(mouseHexPos.row, mouseHexPos.col);
    let oldHover = game.getBoard().setHoverHex(hoverHex);

    if (oldHover === hoverHex) {
      return;
    }

    drawHexNeighborhood([oldHover, hoverHex, game.getBoard().getSelectedHex()]);
  }

  function getCanvasWidth() {
    return p.windowWidth - menuWidth - canvasMargin;
  }

  function getCanvasHeight() {
    return hexRows * hexHeight + hexRadius;
  }

  function drawHexNeighborhood(someHexes) {
    const hexesToDraw = game.getBoard().getHexNeighborhoods(someHexes);
    game.getBoard().getOccupiedHexes().forEach(hex => hexesToDraw.add(hex));

    for (let drawer of drawers) {
      for (let hexToDraw of hexesToDraw) {
        drawer.draw(hexToDraw);
      }
    }
  }

  function pixelToHex(x, y) {
    let col = Math.floor(x / (hexDiameter - (hexRadius / 2)));
    let row;

    if (col % 2 === 0) {
      row = Math.floor(y / hexHeight)
    } else {
      row = Math.floor((y - hexHeight / 2) / hexHeight)
    }

    return { row: row, col: col }; 
  }
});
