import p5 from 'p5';
import { Board } from './board.js';
import { HexDrawer } from './hex-drawer.js';
import { UnitDrawer } from './unit-drawer.js';
import { SelectionDrawer } from './selection-drawer.js';
import { MoveSelectionDrawer } from './selection-drawer.js';
import { MoveArrowDrawer } from './move-arrow-drawer.js';
import { Menu } from './menu.js';
import { Unit } from './unit.js';
import { UnitTypes } from './unit-types.js';
import { Faction, playerTypes } from './faction.js'

const factions = {
  RED: new Faction ('Red Faction', '#C81010' /* red */, playerTypes.CPU),
  BLUE: new Faction('Blue Faction', '#4682B4' /* steel blue */, playerTypes.HUMAN)
}

new p5((p) => {
  const hexRadius = 50;
  const hexHeight = Math.sqrt(3) * hexRadius;
  const hexDiameter = hexRadius * 2;
  const menuWidth = 300;
  const hexRows = 10;
  const canvasMargin = 20;
  
  const board = new Board(10, 10, [factions.RED, factions.BLUE]);
  const hexDraw = new HexDrawer(p, 50);
  hexDraw.setShowHexCoords(true);
  
  const unitDraw = new UnitDrawer(p, hexDraw);
  const selectionDraw = new SelectionDrawer(hexDraw);
  const moveSelectionDraw = new MoveSelectionDrawer(hexDraw);
  const moveArrowDraw = new MoveArrowDrawer(p, hexDraw);
  const drawers = [hexDraw, selectionDraw, moveSelectionDraw, unitDraw, moveArrowDraw];
  const menu = new Menu(board);
  
  const blueUnit = new Unit('Assault Infantry', factions.BLUE, UnitTypes.INFANTRY, 5, 4, 4); 
  board.addUnit(blueUnit, 0, 6);
  
  const redUnit = new Unit('Scout Recon', factions.RED, UnitTypes.RECON, 2, 2, 7);
  board.addUnit(redUnit, 9, 2);

  let canvas;

  p.setup = function() {
    console.log("Let's set it up! ");
    document.getElementById('endTurnBtn').addEventListener('click', menu.doEndTurn.bind(menu));
    canvas = p.createCanvas(getCanvasWidth(), getCanvasHeight());
    canvas.parent('canvas-container');
    menu.setCurrentTurn(factions.RED);
    p.noLoop(); // So that it draws only once  
  };

  p.draw = function() {
    console.log("I'm starting to draw!");
    p.background(90);
  
    for (let currentHex of board.getAllHexes()) {
      hexDraw.draw(currentHex);
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

    const selHexContentsDiv = document.getElementById('selHexContents');
    const selHexCoordDiv = document.getElementById('selHexCoord');

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
    let hexesToDraw = board.getHexNeighborhoods(someHexes);
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
