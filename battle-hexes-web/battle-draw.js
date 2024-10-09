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
    unitDraw.drawHexCounters(currentHex);
  }
}

function windowResized() {
  resizeCanvas(getCanvasWidth(), getCanvasHeight());
}

function hexCenterRc(row, column) {
  oddColumnOffsetX = column * hexRadius / 2;
  oddColumnOffsetY = column % 2 == 0 ? 0 : hexHeight / 2;

  x = hexRadius + column * hexDiameter - oddColumnOffsetX;
  y = hexHeight / 2 + row * hexHeight + oddColumnOffsetY;

  return {x, y};
}

function drawHex(theHex) {
  // console.log(`Drawing ${theHex.row},${theHex.column}`)
  hexCenter = hexCenterRc(theHex.row, theHex.column);
  drawHexagon(hexCenter.x, hexCenter.y, hexRadius, 
              board.isSelected(theHex), board.isHovered(theHex));

  fill(0);
  noStroke();  // No outline for the text
  textSize(16);
  textAlign(CENTER, CENTER);  // Center align text horizontally and vertically    
  text(`${theHex.row}, ${theHex.column}`, hexCenter.x, hexCenter.y);

  if (theHex.units.length) {
    drawCounterRc(theHex.row, theHex.column);
  }
}

function drawHexagon(x, y, radius, selected, hovered) {
  if (selected) {
    stroke(16, 192, 16);
    strokeWeight(6);
  } else if (hovered) {
    stroke(16, 240, 16);
    strokeWeight(6);
  } else {
    stroke(32);
    strokeWeight(2);
  }

  fill(255, 253, 208);  // Set the fill color to cream

  beginShape();
  for (let i = 0; i < 6; i++) {
    let angle = TWO_PI / 6 * i;
    let vx = x + cos(angle) * radius;
    let vy = y + sin(angle) * radius;
    vertex(vx, vy);
  }
  endShape(CLOSE);
}

function drawCounterRc(row, column) {
  counterCenter = hexCenterRc(row, column)
  drawCounter(counterCenter.x, counterCenter.y);
}

function mousePressed() {
  let clickedHexPos = pixelToHex(mouseX, mouseY);
  console.log("Clicked on hex:", clickedHexPos.row, clickedHexPos.col);

  let prevSelectedHex = board.deselect();
  let clickedHex = board.getHex(clickedHexPos.row, clickedHexPos.col);

  if (prevSelectedHex) {
    prevSelectedHex.setSelected(false);
    drawHexNeighborhood(prevSelectedHex);
  }

  if (clickedHex) {
    board.select(clickedHex);
    clickedHex.setSelected(true);
    drawHexNeighborhood(clickedHex);
  }
}

function drawHexNeighborhood(aHex) {
  for (let adjHexCoords of aHex.getAdjacentHexCoords()) {
    let neighborHex = board.getHexStrCoord(adjHexCoords);
    hexDraw.draw(neighborHex);
    selectionDraw.drawHexSelection(neighborHex);
    unitDraw.drawHexCounters(neighborHex);
  }

  hexDraw.draw(aHex);
  selectionDraw.drawHexSelection(aHex);
  unitDraw.drawHexCounters(aHex);
}

function __mousePressed() {
  let clickedHexPos = pixelToHex(mouseX, mouseY);
  console.log("Clicked on hex:", clickedHexPos.row, clickedHexPos.col);

  let prevSelectedHex = board.deselect(); 
  if (prevSelectedHex) {
    drawAdjacent(prevSelectedHex);
    drawHex(prevSelectedHex);
  }

  let clickedHex = board.getHex(clickedHexPos.row, clickedHexPos.col);
  let selHexCoordDiv = document.getElementById('selHexCoord');
  let selHexContentsDiv = document.getElementById('selHexContents');

  if (clickedHex) {
    board.select(clickedHex);
    drawHex(clickedHex);
    if (clickedHex.isEmpty()) {
      selHexContentsDiv.innerHTML = 'Empty Hex';
    } else {
      selHexContentsDiv.innerHTML = 'Hex contains a unit.';
    }
    selHexCoordDiv.innerHTML = `Hex Coord: (${clickedHexPos.row}, ${clickedHexPos.col})`;
  } else {
    selHexContentsDiv.innerHTML = '';
    selHexCoordDiv.innerHTML = '';
  }

  mouseMoved();
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
