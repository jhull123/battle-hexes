import { Faction } from '../../src/model/faction.js';
import { Hex } from '../../src/model/hex.js';
import { Player } from '../../src/player/player.js';
import { Unit } from '../../src/model/unit.js';

const friendlyPlayer = new Player('Friendly Player', 'Human');
const opposingPlayer = new Player('Opposing Player', 'Computer');

let friendlyFaction;
let opposingFaction;
let oppUnit;

beforeEach(() => {
  friendlyFaction = new Faction('Friendlies', "#FF0000", friendlyPlayer);
  friendlyFaction.setOwningPlayer(friendlyPlayer);

  opposingFaction = new Faction('Opp Force', "#0000FF", opposingPlayer);
  opposingFaction.setOwningPlayer(opposingPlayer);
  oppUnit = new Unit('1', 'Opp Unit', opposingFaction, null, 4, 4, 4);
});

describe('move', () => {
  test('throws an error if there are no movement points remaining', () => {
    const unit = new Unit('2', 'Test Unit', friendlyFaction, null, 0, 0, 0);

    expect(() => {
      unit.move(new Hex(), []);
    }).toThrow('No movement points remaining!');
  });

  test('sets moves remaining to zero if adjacent to opponent', () => {
    const unit = new Unit('3', 'Test Unit', friendlyFaction, null, 4, 4, 4);
    const oppHex = new Hex(5, 6);
    oppHex.addUnit(oppUnit);

    unit.move(new Hex(5, 5), [new Hex(4, 5), oppHex]);

    expect(unit.getMovesRemaining()).toBe(0);
  });

  test('decrements move remaining when not oppnent adjacent', () => {
    const unit = new Unit('4', 'Test Unit', friendlyFaction, null, 4, 4, 4);
    unit.move(new Hex(5, 5), [new Hex(4, 5), new Hex(5, 6)]);
    expect(unit.getMovesRemaining()).toBe(3);
  });


  test('deducts terrain move cost when not adjacent to opponent', () => {
    const unit = new Unit('7', 'Test Unit', friendlyFaction, null, 4, 4, 4);
    const destinationHex = new Hex(5, 5);
    destinationHex.setTerrain({ moveCost: 3 });

    unit.move(destinationHex, [new Hex(4, 5), new Hex(5, 6)]);

    expect(unit.getMovesRemaining()).toBe(1);
  });

  test('adds combat opponent when opponent is adjacent', () => {
    const unit = new Unit('5', 'Test Unit', friendlyFaction, null, 4, 4, 4);
    const oppHex = new Hex(5, 6);
    oppHex.addUnit(oppUnit);

    unit.move(new Hex(5, 5), [new Hex(4, 5), oppHex]);

    expect(unit.getCombatOpponents()).toStrictEqual([[oppUnit]]);
  });
});

describe('resetCombat', () => {
  test('combat opponents is empty after reset', () => {
    const unit = new Unit('6', 'Test Unit', friendlyFaction, null, 4, 4, 4);
    const oppHex = new Hex(5, 6);
    oppHex.addUnit(oppUnit);

    unit.move(new Hex(5, 5), [new Hex(4, 5), oppHex]);
    unit.resetCombat();

    expect(unit.getCombatOpponents()).toHaveLength(0);
  });
});
