import { BattleHexesService } from './battle-hexes-service.js';
import { BattleHexesApiError, protocolError } from './battle-hexes-api-error.js';
import { GameCommandCoordinator } from './game-command-coordinator.js';

const positiveInteger = (value) => Number.isInteger(value) && value > 0;

export class HttpBattleHexesService extends BattleHexesService {
  #apiBaseUrl;
  #logServerResponses;
  #uuid;
  #maxAttempts;
  #coordinator;
  #reconciliationHandler = async () => {};
  #versions = new Map();

  constructor({
    apiBaseUrl = process.env.API_URL || 'http://localhost:8000', fetchImpl = fetch,
    logServerResponses = process.env.LOG_SERVER_RESPONSES === 'true',
    uuid = () => globalThis.crypto.randomUUID(), maxAttempts = 3,
    coordinator = new GameCommandCoordinator(),
  } = {}) {
    super();
    this.#apiBaseUrl = apiBaseUrl;
    this.#logServerResponses = logServerResponses;
    this.#uuid = uuid;
    this.#maxAttempts = maxAttempts;
    this.#coordinator = coordinator;
    this.fetchImpl = (fetchImpl === fetch || fetchImpl === globalThis.fetch)
      ? fetchImpl.bind(globalThis) : fetchImpl;
  }

  setReconciliationHandler(handler) {
    this.#reconciliationHandler = handler;
  }

  async #get(path, methodName, gameId = null) {
    let response;
    try {
      response = await this.fetchImpl(`${this.#apiBaseUrl}${path}`);
    } catch {
      throw protocolError('The server response could not be read.');
    }
    const body = await this.#parseResponse(response, path, methodName);
    if (gameId !== null) this.#recordVersion(gameId, response, body);
    return body;
  }

  #post(path, methodName, body, gameId = null) {
    return this.#coordinator.enqueue(gameId ?? '__create__', async () => {
      const expectedGameVersion = gameId === null ? null : this.#versions.get(gameId);
      if (gameId !== null && !positiveInteger(expectedGameVersion)) {
        throw protocolError('No authoritative game version is available.');
      }
      const descriptor = Object.freeze({
        method: 'POST', route: path,
        bodyText: body === undefined ? undefined : JSON.stringify(body),
        idempotencyKey: this.#uuid(), expectedGameVersion,
      });
      return this.#sendDescriptor(descriptor, methodName, gameId);
    }, { awaitResponseApplication: gameId !== null });
  }

  async #sendDescriptor(descriptor, methodName, gameId) {
    let lastError;
    for (let attempt = 0; attempt < this.#maxAttempts; attempt += 1) {
      try {
        const response = await this.fetchImpl(
          `${this.#apiBaseUrl}${descriptor.route}`,
          this.#requestOptions(descriptor),
        );
        const body = await this.#parseResponse(response, descriptor.route, methodName);
        const responseGameId = gameId ?? body.id;
        this.#recordVersion(responseGameId, response, body);
        return body;
      } catch (error) {
        lastError = error;
        if (error instanceof BattleHexesApiError
            && error.code === 'gameVersionConflict' && gameId !== null) {
          const authoritativeGame = await this.#get(`/games/${gameId}`, 'getGame', gameId);
          await this.#reconciliationHandler(authoritativeGame);
          throw error;
        }
        if (!this.#retryable(error) || attempt + 1 === this.#maxAttempts) throw error;
      }
    }
    throw lastError;
  }

  #requestOptions(descriptor) {
    const headers = {
      'Content-Type': 'application/json',
      'Idempotency-Key': descriptor.idempotencyKey,
    };
    if (descriptor.expectedGameVersion !== null) {
      headers['Expected-Game-Version'] = String(descriptor.expectedGameVersion);
    }
    const options = { method: descriptor.method, headers };
    if (descriptor.bodyText !== undefined) options.body = descriptor.bodyText;
    return options;
  }

  async #parseResponse(response, path, methodName) {
    let body;
    try {
      body = await response.json();
    } catch {
      throw protocolError('The server returned an invalid JSON response.', response?.status ?? null);
    }
    if (!response?.ok) {
      if (!body || typeof body !== 'object' || typeof body.code !== 'string') {
        throw protocolError('The server returned an invalid error response.', response?.status ?? null);
      }
      const detail = typeof body.detail === 'string' ? body.detail : body.message;
      throw new BattleHexesApiError({ ...body, status: response.status, message: detail });
    }
    if (this.#logServerResponses) {
      console.info(`server response for ${methodName}: ${JSON.stringify(body)}`);
    }
    return body;
  }

  #recordVersion(gameId, response, body) {
    const headerValue = response.headers?.get?.('Game-Version');
    const version = Number(headerValue);
    const projections = this.#collectVersions(body);
    if (!/^\d+$/.test(headerValue ?? '') || !positiveInteger(version)
        || projections.length === 0 || projections.some((value) => value !== version)) {
      throw protocolError('The server returned an inconsistent game version.', response.status);
    }
    this.#versions.set(gameId, version);
  }

  #collectVersions(value, result = []) {
    if (Array.isArray(value)) value.forEach((item) => this.#collectVersions(item, result));
    else if (value && typeof value === 'object') {
      for (const [key, child] of Object.entries(value)) {
        if (key === 'gameVersion') result.push(child);
        else this.#collectVersions(child, result);
      }
    }
    return result;
  }

  #retryable(error) {
    return !(error instanceof BattleHexesApiError) || error.code === 'gamePersistenceUnavailable';
  }

  listScenarios() { return this.#get('/scenarios', 'listScenarios'); }
  listPlayerTypes() { return this.#get('/player-types', 'listPlayerTypes'); }
  createGame(config) { return this.#post('/games', 'createGame', config); }
  getGame(gameId) { return this.#get(`/games/${gameId}`, 'getGame', gameId); }
  acknowledgeResponseApplication(gameId) {
    this.#coordinator.acknowledgeResponseApplication(gameId);
  }
  resolveHumanMove(gameId, body) { return this.#post(`/games/${gameId}/move`, 'resolveHumanMove', body, gameId); }
  generateCpuMovement(gameId) { return this.#post(`/games/${gameId}/movement`, 'generateCpuMovement', undefined, gameId); }
  resolveCombat(gameId, body) { return this.#post(`/games/${gameId}/combat`, 'resolveCombat', body, gameId); }
  endMovement(gameId, body) { return this.#post(`/games/${gameId}/end-movement`, 'endMovement', body, gameId); }
  endTurn(gameId, body) { return this.#post(`/games/${gameId}/end-turn`, 'endTurn', body, gameId); }
}
