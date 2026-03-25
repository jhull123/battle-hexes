import { BattleHexesService } from './battle-hexes-service.js';

export class HttpBattleHexesService extends BattleHexesService {
  #apiBaseUrl;
  #logServerResponses;

  constructor({
    apiBaseUrl = process.env.API_URL || 'http://localhost:8000',
    fetchImpl = fetch,
    logServerResponses = process.env.LOG_SERVER_RESPONSES === 'true',
  } = {}) {
    super();
    this.#apiBaseUrl = apiBaseUrl;
    this.#logServerResponses = logServerResponses;

    // In browsers, fetch is a host method that must be called with the global object
    // as `this`; keep it bound to avoid "Illegal invocation" errors.
    if (fetchImpl === fetch || fetchImpl === globalThis.fetch) {
      this.fetchImpl = fetchImpl.bind(globalThis);
    } else {
      this.fetchImpl = fetchImpl;
    }
  }

  async #get(path, methodName) {
    const response = await this.fetchImpl(`${this.#apiBaseUrl}${path}`);
    return this.#parseJsonResponse(response, path, methodName);
  }

  async #post(path, methodName, body) {
    const options = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    };

    if (body !== undefined) {
      options.body = JSON.stringify(body);
    }

    const response = await this.fetchImpl(`${this.#apiBaseUrl}${path}`, options);
    return this.#parseJsonResponse(response, path, methodName);
  }

  async #parseJsonResponse(response, path, methodName) {
    if (!response?.ok) {
      console.error(`BattleHexesService HTTP error for ${path}:`, response?.status);
      throw new Error(`Unexpected status ${response?.status ?? 'unknown'}`);
    }

    const responseBody = await response.json();

    if (this.#logServerResponses) {
      console.info(`server response for ${methodName}: ${JSON.stringify(responseBody)}`);
    }

    return responseBody;
  }

  listScenarios() { return this.#get('/scenarios', 'listScenarios'); }
  listPlayerTypes() { return this.#get('/player-types', 'listPlayerTypes'); }
  createGame(config) { return this.#post('/games', 'createGame', config); }
  getGame(gameId) { return this.#get(`/games/${gameId}`, 'getGame'); }
  resolveHumanMove(gameId, sparseBoard) { return this.#post(`/games/${gameId}/move`, 'resolveHumanMove', sparseBoard); }
  generateCpuMovement(gameId) { return this.#post(`/games/${gameId}/movement`, 'generateCpuMovement'); }
  resolveCombat(gameId, sparseBoard) { return this.#post(`/games/${gameId}/combat`, 'resolveCombat', sparseBoard); }
  endMovement(gameId, sparseBoard) { return this.#post(`/games/${gameId}/end-movement`, 'endMovement', sparseBoard); }
  endTurn(gameId, sparseBoard) { return this.#post(`/games/${gameId}/end-turn`, 'endTurn', sparseBoard); }
}
