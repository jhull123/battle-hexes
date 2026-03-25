/**
 * Runtime contract for frontend/backend interactions.
 *
 * Implementations must provide Promise-returning methods with these names:
 * - listScenarios()
 * - listPlayerTypes()
 * - createGame(config)
 * - getGame(gameId)
 * - resolveHumanMove(gameId, sparseBoard)
 * - generateCpuMovement(gameId)
 * - resolveCombat(gameId, sparseBoard)
 * - endMovement(gameId, sparseBoard)
 * - endTurn(gameId, sparseBoard)
 */
export class BattleHexesService {
  listScenarios() { throw new Error('Not implemented'); }
  listPlayerTypes() { throw new Error('Not implemented'); }
  createGame() { throw new Error('Not implemented'); }
  getGame() { throw new Error('Not implemented'); }
  resolveHumanMove() { throw new Error('Not implemented'); }
  generateCpuMovement() { throw new Error('Not implemented'); }
  resolveCombat() { throw new Error('Not implemented'); }
  endMovement() { throw new Error('Not implemented'); }
  endTurn() { throw new Error('Not implemented'); }
}
