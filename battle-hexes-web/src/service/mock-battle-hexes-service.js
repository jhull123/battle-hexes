import { BattleHexesService } from './battle-hexes-service.js';

const MOCK_SCENARIOS = [
  {
    id: 'mock_scenario',
    name: 'Mock Scenario',
    description: 'Offline placeholder scenario.',
    victory: {
      description: 'Hold objectives until turn limit.',
    },
  },
];

const MOCK_PLAYER_TYPES = [
  { id: 'human', name: 'Human' },
  { id: 'random', name: 'Random AI' },
];

const emptyMovementPayload = {
  plans: [],
  sparse_board: { units: [] },
  game: { board: { units: [] } },
  scores: {},
  turnNumber: 1,
  turnLimit: null,
};

export class MockBattleHexesService extends BattleHexesService {
  listScenarios() { return Promise.resolve([...MOCK_SCENARIOS]); }
  listPlayerTypes() { return Promise.resolve([...MOCK_PLAYER_TYPES]); }
  createGame() { return Promise.resolve({ id: 'mock-game' }); }

  getGame(gameId) {
    return Promise.resolve({
      id: gameId || 'mock-game',
      phases: ['Movement', 'Combat', 'End Turn'],
      currentPhase: 'Movement',
      players: [],
      board: { rows: 1, columns: 1, hexes: [], units: [], roads: [] },
      scores: {},
      turnNumber: 1,
      turnLimit: null,
    });
  }

  resolveHumanMove() { return Promise.resolve({ ...emptyMovementPayload }); }
  generateCpuMovement() { return Promise.resolve({ ...emptyMovementPayload }); }
  endMovement() { return Promise.resolve({ ...emptyMovementPayload }); }

  resolveCombat() {
    return Promise.resolve({
      units: [],
      last_combat_results: [],
      scores: {},
      turnNumber: 1,
      turnLimit: null,
    });
  }

  endTurn() {
    return Promise.resolve({
      scores: {},
      turnNumber: 1,
      turnLimit: null,
    });
  }
}
