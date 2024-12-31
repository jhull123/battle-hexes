import p5 from 'p5';
import { Board } from './board.js';
import { Game } from './model/game.js';
import { HexDrawer } from './hex-drawer.js';
import { UnitDrawer } from './unit-drawer.js';
import { SelectionDrawer } from './selection-drawer.js';
import { MoveSelectionDrawer } from './selection-drawer.js';
import { CombatSelectionDrawer } from './selection-drawer.js';
import { MoveArrowDrawer } from './move-arrow-drawer.js';
import { Menu } from './menu.js';
import { Unit } from './unit.js';
import { UnitTypes } from './unit-types.js';
import { Faction, playerTypes } from './faction.js';
import './styles/menu.css';

const factions = {
  RED: new Faction ('Red Faction', '#C81010' /* red */, playerTypes.HUMAN),
  BLUE: new Faction('Blue Faction', '#4682B4' /* steel blue */, playerTypes.CPU)
}

new p5((p) => {
  const hexRadius = 50;
  const hexHeight = Math.sqrt(3) * hexRadius;
  const hexDiameter = hexRadius * 2;
  const menuWidth = 300;
  const hexRows = 10;
  const canvasMargin = 20;
  
  const board = new Board(10, 10, [factions.RED, factions.BLUE]);
  const game = new Game(['Movement', 'Combat'], [factions.RED, factions.BLUE]);
  const menu = new Menu(game, board);

  const hexDrawWithCoords = new HexDrawer(p, hexRadius);
  hexDrawWithCoords.setShowHexCoords(true);
  const hexDraw = new HexDrawer(p, hexRadius);
  
  const unitDraw = new UnitDrawer(p, hexDraw);
  const combatSelectionDraw = new CombatSelectionDrawer(new HexDrawer(p, hexRadius));
  const selectionDraw = new SelectionDrawer(hexDraw);
  const moveSelectionDraw = new MoveSelectionDrawer(hexDraw);
  const moveArrowDraw = new MoveArrowDrawer(p, hexDraw);
  const drawers = [hexDrawWithCoords, combatSelectionDraw, selectionDraw, moveSelectionDraw, unitDraw, moveArrowDraw];
  
  const blueUnit = new Unit('Assault Infantry', factions.BLUE, UnitTypes.INFANTRY, 5, 4, 4); 
  board.addUnit(blueUnit, 3, 5);
  
  const redUnit = new Unit('Scout Recon', factions.RED, UnitTypes.RECON, 2, 2, 7);
  board.addUnit(redUnit, 6, 4);

  let canvas;

  p.setup = function() {
    console.log("Let's set it up!");
    document.getElementById('endTurnBtn').addEventListener('click', menu.doEndTurn.bind(menu));
    canvas = p.createCanvas(getCanvasWidth(), getCanvasHeight());
    canvas.parent('canvas-container');
    menu.setCurrentTurn(factions.RED);
    p.noLoop();
  };

  p.draw = function() {
    console.log("I'm starting to draw!");
    p.background(90);
  
    for (let currentHex of board.getAllHexes()) {
      hexDrawWithCoords.draw(currentHex);
    }
  
    for (let currentHex of board.getAllHexes()) {
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

    let clickedHex = board.getHex(clickedHexPos.row, clickedHexPos.col);
    let prevSelectedHex = board.selectHex(clickedHex);

    drawHexNeighborhood([prevSelectedHex, clickedHex]);

    menu.updateMenu();
  }

  p.mouseMoved = function() {
    let mouseHexPos = pixelToHex(p.mouseX, p.mouseY);
    let hoverHex = board.getHex(mouseHexPos.row, mouseHexPos.col);
    let oldHover = board.setHoverHex(hoverHex);

    if (oldHover === hoverHex) {
      return;
    }

    drawHexNeighborhood([oldHover, hoverHex, board.getSelectedHex()]);
  }

  function getCanvasWidth() {
    return p.windowWidth - menuWidth - canvasMargin;
  }

  function getCanvasHeight() {
    return hexRows * hexHeight + hexRadius;
  }

  function drawHexNeighborhood(someHexes) {
    const hexesToDraw = board.getHexNeighborhoods(someHexes);
    board.getOccupiedHexes().forEach(hex => hexesToDraw.add(hex));

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
