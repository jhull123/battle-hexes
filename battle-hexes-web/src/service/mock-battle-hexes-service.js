import { BattleHexesService } from './battle-hexes-service.js';
import { GameCommandCoordinator } from './game-command-coordinator.js';
import getGameResponse from './mock-responses/get-game.json';

const MOCK_SCENARIOS = [{
  id: 'mock_scenario', name: 'Mock Scenario', description: 'Offline placeholder scenario.',
  victory: { description: 'Hold objectives until turn limit.' },
}];
const MOCK_PLAYER_TYPES = [
  { id: 'human', name: 'Human' }, { id: 'random', name: 'Random AI' },
];

export class MockBattleHexesService extends BattleHexesService {
  #versions = new Map();
  #coordinator;
  #errorProvider;

  constructor({ coordinator = new GameCommandCoordinator(), errorProvider = () => null } = {}) {
    super();
    this.#coordinator = coordinator;
    this.#errorProvider = errorProvider;
  }

  listScenarios() { return Promise.resolve(structuredClone(MOCK_SCENARIOS)); }
  listPlayerTypes() { return Promise.resolve(structuredClone(MOCK_PLAYER_TYPES)); }

  createGame() {
    return this.#coordinator.enqueue('__create__', async () => {
      this.#throwInjected('createGame');
      this.#versions.set('mock-game', 1);
      return { ...structuredClone(getGameResponse), id: 'mock-game', gameVersion: 1 };
    });
  }

  getGame(gameId) {
    const version = this.#versions.get(gameId) ?? 1;
    this.#versions.set(gameId, version);
    return Promise.resolve({ ...structuredClone(getGameResponse), gameVersion: version });
  }

  #command(gameId, operation, response = {}) {
    return this.#coordinator.enqueue(gameId, async () => {
      this.#throwInjected(operation);
      const gameVersion = (this.#versions.get(gameId) ?? 1) + 1;
      this.#versions.set(gameId, gameVersion);
      return { ...structuredClone(response), gameVersion };
    });
  }

  #throwInjected(operation) {
    const error = this.#errorProvider(operation);
    if (error) throw error;
  }

  #movement(gameId, operation) {
    const response = {
      plans: [], sparseBoard: { units: [] }, scores: {}, turnNumber: 1, turnLimit: null,
    };
    return this.#command(gameId, operation, response).then((result) => ({
      ...result,
      sparseBoard: { ...result.sparseBoard, gameVersion: result.gameVersion },
    }));
  }

  resolveHumanMove(gameId) { return this.#movement(gameId, 'resolveHumanMove'); }
  generateCpuMovement(gameId) { return this.#movement(gameId, 'generateCpuMovement'); }
  endMovement(gameId) { return this.#movement(gameId, 'endMovement'); }
  resolveCombat(gameId) { return this.#command(gameId, 'resolveCombat', { units: [], lastCombatResults: [], scores: {} }); }
  endTurn(gameId) {
    return this.#command(gameId, 'endTurn', structuredClone(getGameResponse))
      .then((result) => ({ ...result, id: gameId }));
  }
}
