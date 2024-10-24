const hexRadius = 50;
const hexHeight = Math.sqrt(3) * hexRadius;
const hexDiameter = hexRadius * 2;
const counterSide = hexRadius + hexRadius * 0.3;
const counterSideThird = counterSide / 3;
const menuWidth = 300;
const hexRows = 10;
const canvasMargin = 20;

const board = new Board(10, 10);
const hexDraw = new HexDrawer(50);
hexDraw.setShowHexCoords(true);

const unitDraw = new UnitDrawer(hexDraw);
const selectionDraw = new SelectionDrawer(hexDraw);
const moveSelectionDraw = new MoveSelectionDrawer(hexDraw);
const moveArrowDraw = new MoveArrowDrawer(hexDraw);
const drawers = [hexDraw, selectionDraw, moveSelectionDraw, unitDraw, moveArrowDraw];

let myHex = board.getHex(5, 5);
myHex.addUnit(new Unit(attack=5, defense=4, move=4));

function setup() {
  let canvas = createCanvas(getCanvasWidth(), getCanvasHeight());
  canvas.parent('canvas-container'); 
  noLoop(); // So that it draws only once
}

function getCanvasWidth() {
  return windowWidth - menuWidth - canvasMargin;
}

function getCanvasHeight() {
  return hexRows * hexHeight + hexRadius;
}

function draw() {
  console.log("I'm starting to draw!");
  background(90);

  for (let currentHex of board.getAllHexes()) {
    hexDraw.draw(currentHex);
  }

  for (let currentHex of board.getAllHexes()) {
    unitDraw.draw(currentHex);
  }
}

function windowResized() {
  resizeCanvas(getCanvasWidth(), getCanvasHeight());
}

function mousePressed() {
  let clickedHexPos = pixelToHex(mouseX, mouseY);
  console.log("Clicked on hex:", clickedHexPos.row, clickedHexPos.col);

  let clickedHex = board.getHex(clickedHexPos.row, clickedHexPos.col);
  let prevSelectedHex = board.selectHex(clickedHex);

  drawHexNeighborhood([prevSelectedHex, clickedHex]);

  const selHexContentsDiv = document.getElementById('selHexContents');
  const selHexCoordDiv = document.getElementById('selHexCoord');

  if (clickedHex === undefined) {
    // nothing here!
  } else if (clickedHex.isEmpty()) {
    selHexContentsDiv.innerHTML = 'Empty Hex';
    selHexCoordDiv.innerHTML = `Hex Coord: (${clickedHexPos.row}, ${clickedHexPos.col})`;
  } else {
    selHexContentsDiv.innerHTML = 'Hex contains a unit.';
    selHexCoordDiv.innerHTML = `Hex Coord: (${clickedHexPos.row}, ${clickedHexPos.col})`;
  }
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

function mouseMoved() {
  let mouseHexPos = pixelToHex(mouseX, mouseY);
  let hoverHex = board.getHex(mouseHexPos.row, mouseHexPos.col);
  let oldHover = board.setHoverHex(hoverHex);

  if (oldHover === hoverHex) {
    return;
  }

  drawHexNeighborhood([oldHover, hoverHex, board.getSelectedHex()]);
}

function pixelToHex2(x, y) {
  let col = Math.floor(x / hexHeight);
  let row;

  // Adjust row depending on whether it's an even or odd column
  if (col % 2 === 0) {
    row = Math.floor(y / hexDiameter);
  } else {
    row = Math.floor((y - hexDiameter / 2) / hexDiameter);
  }

  return { row: row, col: col };
}
