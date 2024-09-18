const hexRadius = 50;
const hexHeight = Math.sqrt(3) * hexRadius;
const hexDiameter = hexRadius * 2;
const counterSide = hexRadius + hexRadius * 0.3;
const counterSideThird = counterSide / 3;
const menuWidth = 300;
const hexRows = 10;
const canvasMargin = 20;

var board = new Board(10, 10);
myHex = board.getHex(5, 5);
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
    drawHex(currentHex);
  }

  for (let currentHex of board.getAllHexes()) {
    if (currentHex.units.length) {
      drawCounterRc(currentHex.row, currentHex.column);
    }
  }
}

function windowResized() {
  resizeCanvas(getCanvasWidth(), getCanvasHeight());
}

function drawHexFull(theHex) {
  drawHex(theHex);
  if (theHex.units.length) {
    drawCounterRc(theHex.row, theHex.column);
  }
}

function hexCenterRc(row, column) {
  oddColumnOffsetX = column * hexRadius / 2;
  oddColumnOffsetY = column % 2 == 0 ? 0 : hexHeight / 2;

  x = hexRadius + column * hexDiameter - oddColumnOffsetX;
  y = hexHeight / 2 + row * hexHeight + oddColumnOffsetY;

  return {x, y};
}

function drawHex(theHex) {
  hexCenter = hexCenterRc(theHex.row, theHex.column);
  drawHexagon(hexCenter.x, hexCenter.y, hexRadius, board.isSelected(theHex));

  fill(0);  // Set the text color to black
  noStroke();  // No outline for the text
  textSize(16);  // Set text size
  textAlign(CENTER, CENTER);  // Center align text horizontally and vertically    
  text(`${theHex.row}, ${theHex.column}`, hexCenter.x, hexCenter.y);
}

function drawHexagon(x, y, radius, selected) {
  if (selected) {
    stroke(16, 256, 16);
  } else {
    stroke(32);
  }

  strokeWeight(2);
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

/* x and y are the center of the square. side is the square side length.
 */
function drawCounter(x, y) {
  stroke(96, 32, 32);
  strokeWeight(3);
  fill(200, 16, 16);

  rectMode(CENTER);
  rect(x, y, counterSide, counterSide, 3);

  drawInfantrySymbol(x, y, counterSide / 2, counterSideThird);
  drawUnitStats(x, y);
  drawUnitSize(x, y);
}

function drawInfantrySymbol(x, y, width, height) {
  stroke(255)
  strokeWeight(2);
  rect(x, y, width, height);

  let halfWidth = width / 2;
  let halfHeight = height / 2;

  stroke(255);
  strokeWeight(2);

  // Draw "X" by connecting the corners of the smaller rectangle
  line(x - halfWidth, y - halfHeight, x + halfWidth, y + halfHeight);
  line(x + halfWidth, y - halfHeight, x - halfWidth, y + halfHeight);
}

function drawUnitStats(x, y) {
  fill(255);
  noStroke();
  textSize(14);
  textAlign(CENTER, CENTER);    
  text('4-4-4', x, y + counterSideThird);
}

function drawUnitSize(x, y) {
  fill(255);
  noStroke();
  textSize(9);
  textAlign(CENTER, CENTER);
  text('XX', x, y - counterSideThird + counterSideThird * 0.2);
}

function mousePressed() {
  let clickedHexPos = pixelToHex(mouseX, mouseY);
  console.log("Clicked on hex:", clickedHexPos.row, clickedHexPos.col);

  let prevSelectedHex = board.deselect(); 
  if (prevSelectedHex) {
    drawHexFull(prevSelectedHex);
  }

  let clickedHex = board.getHex(clickedHexPos.row, clickedHexPos.col);
  if (clickedHex) {
    board.select(clickedHex);
    drawHexFull(clickedHex);
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