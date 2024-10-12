const { Hex } = require('../battle'); // Assuming you are exporting Hex from battle.js

describe('Hex class', () => {
  test('should create a Hex with the given coordinates', () => {
    const hex = new Hex(3, 5);
    expect(hex.x).toBe(3);
    expect(hex.y).toBe(5);
  });
});
