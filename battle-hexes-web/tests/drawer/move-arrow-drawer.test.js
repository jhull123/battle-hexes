import { MoveArrowDrawer } from '../../src/drawer/move-arrow-drawer.js';

function createP5Mock() {
  return {
    PI: Math.PI,
    CLOSE: 'close',
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    fill: jest.fn(),
    atan2: Math.atan2,
    push: jest.fn(),
    pop: jest.fn(),
    translate: jest.fn(),
    rotate: jest.fn(),
    beginShape: jest.fn(),
    vertex: jest.fn(),
    endShape: jest.fn(),
  };
}

describe('MoveArrowDrawer', () => {
  test('does not draw hover arrow for stacking-illegal destination', () => {
    const p = createP5Mock();
    const hexDrawer = {
      getHexRadius: () => 10,
      hexCenter: () => ({ x: 5, y: 5 }),
    };
    const moveArrowDrawer = new MoveArrowDrawer(p, hexDrawer);

    const fromHex = {
      hasMovableUnit: () => true,
    };
    const targetHex = {
      isEmpty: () => true,
      getMoveHoverIllegalReason: () => 'STACKING_LIMIT_EXCEEDED',
      getMoveHoverFromHex: () => fromHex,
    };

    moveArrowDrawer.draw(targetHex);

    expect(p.beginShape).not.toHaveBeenCalled();
  });
});
