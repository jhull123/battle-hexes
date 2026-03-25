import { BattleHexesService } from './battle-hexes-service.js';

export class HttpBattleHexesService extends BattleHexesService {
  #apiBaseUrl;

  constructor({ apiBaseUrl = process.env.API_URL || 'http://localhost:8000', fetchImpl = fetch } = {}) {
    super();
    this.#apiBaseUrl = apiBaseUrl;
    this.fetchImpl = fetchImpl;
  }

  async #get(path) {
    const response = await this.fetchImpl(`${this.#apiBaseUrl}${path}`);
    return this.#parseJsonResponse(response, path);
  }

  async #post(path, body) {
    const options = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    };

    if (body !== undefined) {
      options.body = JSON.stringify(body);
    }

    const response = await this.fetchImpl(`${this.#apiBaseUrl}${path}`, options);
    return this.#parseJsonResponse(response, path);
  }

  async #parseJsonResponse(response, path) {
    if (!response?.ok) {
      console.error(`BattleHexesService HTTP error for ${path}:`, response?.status);
      throw new Error(`Unexpected status ${response?.status ?? 'unknown'}`);
    }

    return response.json();
  }

  listScenarios() { return this.#get('/scenarios'); }
  listPlayerTypes() { return this.#get('/player-types'); }
  createGame(config) { return this.#post('/games', config); }
  getGame(gameId) { return this.#get(`/games/${gameId}`); }
  resolveHumanMove(gameId, sparseBoard) { return this.#post(`/games/${gameId}/move`, sparseBoard); }
  generateCpuMovement(gameId) { return this.#post(`/games/${gameId}/movement`); }
  resolveCombat(gameId, sparseBoard) { return this.#post(`/games/${gameId}/combat`, sparseBoard); }
  endMovement(gameId, sparseBoard) { return this.#post(`/games/${gameId}/end-movement`, sparseBoard); }
  endTurn(gameId, sparseBoard) { return this.#post(`/games/${gameId}/end-turn`, sparseBoard); }
}
