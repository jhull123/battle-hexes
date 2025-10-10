import p5 from 'p5';
import { eventBus } from './event-bus.js';
import { Game } from './model/game.js';
import { HexDrawer } from './drawer/hex-drawer.js';
import { UnitDrawer } from './drawer/unit-drawer.js';
import { SelectionDrawer } from './drawer/selection-drawer.js';
import { MoveSelectionDrawer } from './drawer/selection-drawer.js';
import { CombatSelectionDrawer } from './drawer/selection-drawer.js';
import { MoveArrowDrawer } from './drawer/move-arrow-drawer.js';
import { Menu } from './menu.js';
import './styles/menu.css';
import { GameCreator } from './model/game-creator.js';

const extractGameIdFromLocation = () => {
  const pathMatch = window.location.pathname.match(/battle(?:\.html)?\/([^/?#]+)/);
  if (pathMatch && pathMatch[1]) {
    return pathMatch[1];
  }

  const params = new URLSearchParams(window.location.search);
  return params.get('gameId');
};

const updateHistoryWithGameId = (gameId) => {
  const params = new URLSearchParams(window.location.search);
  const query = params.toString();
  const basePath = window.location.pathname.replace(/[^/]*$/, '');
  const targetPath = `${basePath}battle/${gameId}${query ? `?${query}` : ''}`;
  window.history.replaceState(null, '', targetPath);
};

const loadGameData = async () => {
  const existingGameId = extractGameIdFromLocation();
  if (existingGameId) {
    const gameData = await Game.fetchGameFromServer(existingGameId);
    updateHistoryWithGameId(gameData.id);
    return gameData;
  }

  const defaultGame = await Game.newGameFromServer();
  const params = new URLSearchParams(window.location.search);
  const query = params.toString();
  const targetUrl = `battle.html?gameId=${encodeURIComponent(defaultGame.id)}${query ? `&${query}` : ''}`;
  window.location.replace(targetUrl);
  return defaultGame;
};

const gameData = await loadGameData();
console.log('game data: ' + JSON.stringify(gameData));

new p5((p) => {
  const hexRadius = 50;
  const hexHeight = Math.sqrt(3) * hexRadius;
  const hexDiameter = hexRadius * 2;
  const menuWidth = 300;
  const hexRows = 10;
  const canvasMargin = 20;
  
  const game = new GameCreator().createGame(gameData);
  const menu = new Menu(game);

  if (!game.getCurrentPlayer().isHuman()) {
    game.getCurrentPlayer().play(game);
  }

  const hexDrawWithCoords = new HexDrawer(p, hexRadius);
  hexDrawWithCoords.setShowHexCoords(menu.getShowHexCoordsPreference());
  const hexDraw = new HexDrawer(p, hexRadius);
  
  const unitDraw = new UnitDrawer(p, hexDraw);
  const combatSelectionDraw = new CombatSelectionDrawer(new HexDrawer(p, hexRadius));
  const selectionDraw = new SelectionDrawer(hexDraw);
  const moveSelectionDraw = new MoveSelectionDrawer(hexDraw);
  const moveArrowDraw = new MoveArrowDrawer(p, hexDraw);
  const drawers = [hexDrawWithCoords, combatSelectionDraw, selectionDraw, moveSelectionDraw, unitDraw, moveArrowDraw];

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
  
    for (let currentHex of game.getBoard().getAllHexes()) {
      hexDrawWithCoords.draw(currentHex);
    }
  
    for (let currentHex of game.getBoard().getAllHexes()) {
      unitDraw.draw(currentHex);
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
