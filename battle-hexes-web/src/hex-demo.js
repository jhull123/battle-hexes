import p5 from 'p5';
import { HexDrawer } from './drawer/hex-drawer.js';
import { VillageDrawer } from './drawer/village-drawer.js';

const hexRadius = 40;

const demoHexes = [
  { row: 0, column: 0 },
  { row: 0, column: 1 },
  { row: 0, column: 2 },
  { row: 1, column: 0 },
  { row: 1, column: 1, terrain: 'village' },
  { row: 1, column: 2 },
  { row: 2, column: 1 },
  { row: 2, column: 2 },
];

new p5((p) => {
  const hexDrawer = new HexDrawer(p, hexRadius);
  const villageDrawer = new VillageDrawer(p, hexDrawer);

  const canvasPadding = 30;

  p.setup = function() {
    const canvas = p.createCanvas(getCanvasWidth(), getCanvasHeight());
    canvas.parent('hex-demo-canvas');
    p.noLoop();
  };

  p.draw = function() {
    p.background('#f4f7fb');

    demoHexes.forEach((hex) => {
      if (hex.terrain === 'village') {
        villageDrawer.draw(hex);
      } else {
        hexDrawer.draw(hex);
      }
    });
  };

  function getCanvasWidth() {
    const columns = Math.max(...demoHexes.map((hex) => hex.column)) + 1;
    const hexDiameter = hexDrawer.getHexRadius() * 2;
    const overlap = hexDrawer.getHexRadius() / 2;
    return columns * hexDiameter - overlap * (columns - 1) + canvasPadding * 2;
  }

  function getCanvasHeight() {
    const rows = Math.max(...demoHexes.map((hex) => hex.row)) + 1;
    const hexHeight = Math.sqrt(3) * hexDrawer.getHexRadius();
    return rows * hexHeight + hexDrawer.getHexRadius() + canvasPadding;
  }
});
