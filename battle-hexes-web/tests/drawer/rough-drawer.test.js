import { RoughDrawer } from '../../src/terraindraw/rough-drawer.js';

const createMockP5 = () => ({
  TWO_PI: Math.PI * 2,
  cos: Math.cos,
  sin: Math.sin,
  random: jest.fn((min, max) => {
    if (typeof min === 'undefined') {
      return 0.5;
    }

    if (typeof max === 'undefined') {
      return min * 0.5;
    }

    return min + (max - min) * 0.5;
  }),
  fill: jest.fn(),
  stroke: jest.fn(),
  strokeWeight: jest.fn(),
  // the drawer now uses custom shapes rather than simple circles
  circle: jest.fn(),
  beginShape: jest.fn(),
  vertex: jest.fn(),
  bezierVertex: jest.fn(),
  endShape: jest.fn(),
  background: jest.fn(),
  noFill: jest.fn(),
  randomSeed: jest.fn(),
});

describe('RoughDrawer', () => {
  test('draw renders stipple circles without base hex fill operations', () => {
    const p5 = createMockP5();
    const hexDrawer = {
      hexCenter: jest.fn(() => ({ x: 50, y: 75 })),
      getHexRadius: jest.fn(() => 40),
      drawHex: jest.fn(),
    };
    const drawer = new RoughDrawer(p5, hexDrawer);

    drawer.draw({});

    expect(hexDrawer.hexCenter).toHaveBeenCalled();
    expect(hexDrawer.getHexRadius).toHaveBeenCalled();
    expect(p5.strokeWeight).toHaveBeenCalledWith(1.2);
    expect(p5.fill).toHaveBeenCalled();
    expect(p5.stroke).toHaveBeenCalled();
    // shape-based drawing should have been invoked
    expect(p5.beginShape).toHaveBeenCalled();
    expect(p5.vertex).toHaveBeenCalled();
    expect(p5.bezierVertex).toHaveBeenCalled();
    expect(p5.endShape).toHaveBeenCalledWith(p5.CLOSE);

    const fillArg = p5.fill.mock.calls[0][0];
    const strokeArg = p5.stroke.mock.calls[0][0];
    expect(fillArg).toMatch(/^#(?:5E604E|70735C|8E9076)[0-9A-F]{2}$/);
    expect(strokeArg).toMatch(/^#3E3F33[0-9A-F]{2}$/);

    expect(hexDrawer.drawHex).not.toHaveBeenCalled();
    // background/noFill still shouldn't be called
    expect(p5.background).not.toHaveBeenCalled();
    expect(p5.noFill).not.toHaveBeenCalled();
  });

  test('draw uses minimum stroke weight cap for small hexes', () => {
    const p5 = createMockP5();
    const hexDrawer = {
      hexCenter: jest.fn(() => ({ x: 5, y: 10 })),
      getHexRadius: jest.fn(() => 10),
    };
    const drawer = new RoughDrawer(p5, hexDrawer);

    drawer.draw({});

    expect(p5.strokeWeight).toHaveBeenCalledWith(0.6);
  });
});
