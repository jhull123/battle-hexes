import { Faction } from '../src/faction.js';
import { Unit } from '../src/unit.js';
import { Hex } from '../src/hex.js';

let friendlyFaction;
let opposingFaction;
let oppUnit;

beforeEach(() => {
  friendlyFaction = new Faction('Friendlies');
  opposingFaction = new Faction('Opp Force');
  oppUnit = new Unit('Opp Unit', opposingFaction, null, 4, 4, 4);
});

describe('move', () => {
  test('throws an error if there are no movement points remaining', () => {
    const unit = new Unit('Test Unit', friendlyFaction, null, 0, 0, 0);

    expect(() => {
      unit.move(new Hex(), []);
    }).toThrow('No movement points remaining!');
  });

  test('sets moves remaining to zero if adjacent to opponent', () => {
    const unit = new Unit('Test Unit', friendlyFaction, null, 4, 4, 4);
    const oppHex = new Hex(5, 6);
    oppHex.addUnit(oppUnit);

    unit.move(new Hex(5, 5), [new Hex(4, 5), oppHex]);

    expect(unit.getMovesRemaining()).toBe(0);
  });

  test('decrements move remaining when not oppnent adjacent', () => {
    const unit = new Unit('Test Unit', friendlyFaction, null, 4, 4, 4);
    unit.move(new Hex(5, 5), [new Hex(4, 5), new Hex(5, 6)]);
    expect(unit.getMovesRemaining()).toBe(3);
  });
});
