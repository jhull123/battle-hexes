import { UnitTypeSymbolDrawer } from '../../src/drawer/unit-type-symbol-drawer.js';

describe('UnitTypeSymbolDrawer', () => {
  const createP5Mock = () => ({
    stroke: jest.fn(),
    strokeWeight: jest.fn(),
    rect: jest.fn(),
    line: jest.fn(),
    ellipse: jest.fn(),
  });

  test('draws infantry symbol for infantry units regardless of case', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => 'InFaNtRy' }, 100, 100, 20, 10);

    expect(p5.line).toHaveBeenCalledTimes(2);
    expect(p5.ellipse).not.toHaveBeenCalled();
  });

  test('draws armor symbol for armor units regardless of case', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => 'ArMoR' }, 100, 100, 20, 10);

    expect(p5.rect).toHaveBeenCalledWith(100, 100, 20, 10);
    expect(p5.ellipse).toHaveBeenCalledWith(100, 100, 20, 10);
    expect(p5.line).not.toHaveBeenCalled();
  });

  test('draws fallback symbol for non-infantry units', () => {
    const p5 = createP5Mock();
    const drawer = new UnitTypeSymbolDrawer(p5);

    drawer.draw({ getType: () => 'MG' }, 100, 100, 20, 10);

    expect(p5.rect).toHaveBeenCalledWith(100, 100, 20, 10);
    expect(p5.line).not.toHaveBeenCalled();
    expect(p5.ellipse).not.toHaveBeenCalled();
  });
});
