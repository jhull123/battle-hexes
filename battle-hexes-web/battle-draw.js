const hexRadius = 50;
const hexHeight = Math.sqrt(3) * hexRadius;
const hexDiameter = hexRadius * 2;
const counterSide = hexRadius + hexRadius * 0.3;
const counterSideThird = counterSide / 3;
const menuWidth = 300;
const hexRows = 10;
const canvasMargin = 20;

var board = new Board(10, 10);
var hexDraw = new HexDrawer(50);
hexDraw.setShowHexCoords(true);

var unitDraw = new UnitDrawer(hexDraw);
var selectionDraw = new SelectionDrawer(hexDraw);
const drawers = [hexDraw, selectionDraw, unitDraw];

let myHex = board.getHex(5, 5);
myHex.addUnit(new Unit());

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

  drawHexNeighborhood([oldHover, hoverHex]);
}

function __mouseMoved() {
  let mouseHexPos = pixelToHex(mouseX, mouseY);
  let hoverHex = board.getHex(mouseHexPos.row, mouseHexPos.col);

  let oldHover = board.dehover();
  if (oldHover && oldHover !== hoverHex) {
    drawAdjacent(oldHover);
    drawHex(oldHover);
  }

  if (board.hasSelection() && !board.selectedHex.isEmpty()) {
    if (board.selectedHex.isAdjacent(hoverHex)) {
      console.log(`Adjacent hover hex is ${hoverHex.coordsHumanString()}`);
      board.setMoveHoverHex(hoverHex);
      hoverHightlight = true;
    }
  }

  if (hoverHex === undefined) {
    return;
  }

  drawAdjacent(hoverHex);
  drawHex(hoverHex);

  if (board.hasSelection()) {
    drawHex(board.selectedHex);
  }

  if (board.hasSelection() && hoverHex !== undefined && board.selectedHex !== hoverHex && !board.selectedHex.isEmpty()) {
    drawMoveArrow(board.selectedHex, hoverHex);
  }
}

function drawAdjacent(aHex) {
  for (let strCoords of aHex.getAdjacentHexCoords()) {
    let someHex = board.getHexStrCoord(strCoords);
    if (someHex) {
      if (someHex) {
        drawHex(someHex);
      }
    }
  }  
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

function drawMoveArrow(fromHex, toHex) {
  stroke(0, 208, 0);
  strokeWeight(2);
  fill(16, 240, 16);

  let toCenter = hexCenterRc(toHex.row, toHex.column);
  let fromCenter = hexCenterRc(fromHex.row, fromHex.column);

  let angle = atan2(toCenter.y - fromCenter.y, toCenter.x - fromCenter.x) + 0.5 * PI;

  let arrowLength = hexRadius;
  let arrowWidth = hexRadius / 2;
  let arrowTop = -0.75 * hexDiameter;

  push();
  translate(fromCenter.x, fromCenter.y);
  rotate(angle);

  beginShape();
  vertex(0, arrowTop); // top of the arrow
  vertex(-arrowWidth / 2, arrowTop + arrowLength / 3);  // Left side 1
  vertex(-arrowWidth / 4, arrowTop + arrowLength / 3);  // Left side 2
  vertex(-arrowWidth / 4, arrowTop + arrowLength);      // Left side 3
  vertex(arrowWidth / 4, arrowTop + arrowLength);       // Right side 3
  vertex(arrowWidth / 4, arrowTop + arrowLength / 3);   // Right side 2
  vertex(arrowWidth / 2, arrowTop + arrowLength / 3);   // Right side 1
  endShape(CLOSE);

  pop();
}
