import { Board } from "../src/board";
import { CpuPlayer } from "../src/cpu-player";
import { Faction } from "../src/faction";
import { Unit } from "../src/unit";

let humanFaction, cpuFaction, board, humanUnit, cpuUnit, cpuPlayer;

beforeEach(() => {
  humanFaction = new Faction('Human');
  cpuFaction = new Faction('CPU');
  board = new Board(10, 10, [humanFaction, cpuFaction]);
  humanUnit = new Unit('Human Unit', humanFaction, null, 4, 4, 4);
  cpuUnit = new Unit('CPU Unit', cpuFaction, null, 4, 4, 4);
  cpuPlayer = new CpuPlayer(board, cpuFaction);

  board.addUnit(cpuUnit, 3, 3);
  board.addUnit(humanUnit, 6, 6);
});

describe('movement', () => {
  test('CPU movement moves CPU controlled units', () => {
    cpuPlayer.movement();
  });
});