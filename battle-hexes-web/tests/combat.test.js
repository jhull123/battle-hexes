import { Combat } from "../src/combat";
import { Faction } from "../src/faction";
import { Hex } from "../src/hex";
import { Unit } from "../src/unit";

let hexes, factions;

beforeEach(() => {
  hexes = new Array();
  factions = [new Faction('Faction One'), new Faction('Faction Two')];
});

describe('hasCombat', () => {
  test('hasCombat() is false when units are not adjacent', () => {
    const combat = new Combat(hexes, factions[0]);
    // TODO!!!
  });
});