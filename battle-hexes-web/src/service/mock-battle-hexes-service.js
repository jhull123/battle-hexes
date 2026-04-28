import { BattleHexesService } from './battle-hexes-service.js';
import getGameResponse from './mock-responses/get-game.json';

const MOCK_SCENARIOS = [
  {
    id: 'mock_scenario',
    name: 'Mock Scenario',
    description: 'Offline placeholder scenario.',
    stacking_limit: 2,
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
  listScenarios() {
    console.log('Returning mock response for listScenarios.');
    return Promise.resolve([...MOCK_SCENARIOS]);
  }

  listPlayerTypes() {
    console.log('Returning mock response for listPlayerTypes.');
    return Promise.resolve([...MOCK_PLAYER_TYPES]);
  }

  createGame() {
    console.log('Returning mock response for createGame.');
    return Promise.resolve({ id: 'mock-game' });
  }

  getGame(gameId) {
    console.log('Returning mock response for getGame.');
    void gameId;
    return Promise.resolve(JSON.parse(JSON.stringify(getGameResponse)));
  }

  resolveHumanMove() {
    console.log('Returning mock response for resolveHumanMove.');
    return Promise.resolve({ ...emptyMovementPayload });
  }

  generateCpuMovement() {
    console.log('Returning mock response for generateCpuMovement.');
    return Promise.resolve({ ...emptyMovementPayload });
  }
  
  endMovement() {
    console.log('Returning mock response for endMovement.');
    return Promise.resolve({ ...emptyMovementPayload });
  }

  resolveCombat() {
    console.log('Returning mock response for resolveCombat.');
    return Promise.resolve({
      units: [],
      last_combat_results: [],
      scores: {},
      turnNumber: 1,
      turnLimit: null,
    });
  }

  endTurn() {
    console.log('Returning mock response for endTurn.');
    return Promise.resolve({
      scores: {},
      turnNumber: 1,
      turnLimit: null,
    });
  }
}
