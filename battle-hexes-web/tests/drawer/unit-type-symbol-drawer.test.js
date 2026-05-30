import { UnitTypeSymbolDrawer } from '../../src/drawer/unit-type-symbol-drawer.js';

describe('UnitTypeSymbolDrawer', () => {
  const createP5Mock = () => ({
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    noFill: jest.fn(),
    rect: jest.fn(),
    line: jest.fn(),
    arc: jest.fn(),
    ellipse: jest.fn(),
    PI: Math.PI,
    TWO_PI: Math.PI * 2,
  });

  test('draws infantry symbol for infantry units regardless of case', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => 'InFaNtRy' }, 100, 100, 20, 10);

    expect(p5.line).toHaveBeenCalledTimes(2);
    expect(p5.arc).not.toHaveBeenCalled();
    expect(p5.ellipse).not.toHaveBeenCalled();
  });

  test('draws airborne infantry symbol with infantry X and a subtle double-hump marker', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => '  PaRaChUtE InFaNtRy  ' }, 100, 100, 20, 10);

    expect(p5.rect).toHaveBeenCalledWith(100, 100, 20, 10);
    expect(p5.line).toHaveBeenCalledTimes(2);
    expect(p5.arc).toHaveBeenCalledTimes(2);
    expect(p5.strokeWeight).toHaveBeenLastCalledWith(2);
    expect(p5.noFill).toHaveBeenCalled();
    expect(p5.ellipse).not.toHaveBeenCalled();
  });

  test('draws armor symbol as a centered capsule inside the outer box', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => 'ArMoR' }, 100, 100, 20, 10);

    expect(p5.rect).toHaveBeenNthCalledWith(1, 100, 100, 20, 10);
    expect(p5.rect).toHaveBeenNthCalledWith(2, 100, 100, 14, 4, 2);
    expect(p5.noFill).toHaveBeenCalled();
    expect(p5.line).not.toHaveBeenCalled();
    expect(p5.arc).not.toHaveBeenCalled();
    expect(p5.ellipse).not.toHaveBeenCalled();
  });

  test('draws fallback symbol for non-infantry units', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => 'engineer' }, 100, 100, 20, 10);

    expect(p5.rect).toHaveBeenCalledWith(100, 100, 20, 10);
    expect(p5.line).not.toHaveBeenCalled();
    expect(p5.arc).not.toHaveBeenCalled();
    expect(p5.ellipse).not.toHaveBeenCalled();
  });

  test('draws MG symbol as infantry with a thin lower-third support bar', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => 'MG' }, 100, 100, 20, 10);

    expect(p5.rect).toHaveBeenCalledWith(100, 100, 20, 10);
    expect(p5.strokeWeight).toHaveBeenLastCalledWith(2);
    expect(p5.arc).not.toHaveBeenCalled();
    expect(p5.ellipse).not.toHaveBeenCalled();
  });

  test('draws machine gun symbol for "machine gun" unit type', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => ' machine gun ' }, 100, 100, 20, 10);

    expect(p5.line).toHaveBeenCalledTimes(3);
    expect(p5.arc).not.toHaveBeenCalled();
    expect(p5.ellipse).not.toHaveBeenCalled();
  });
});
