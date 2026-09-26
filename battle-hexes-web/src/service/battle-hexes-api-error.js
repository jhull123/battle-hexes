export class BattleHexesApiError extends Error {
  constructor({ status = null, code = 'protocolError', message, currentGameVersion, expectedGameVersion }) {
    super(message);
    this.name = 'BattleHexesApiError';
    this.status = status;
    this.code = code;
    if (currentGameVersion !== undefined) this.currentGameVersion = currentGameVersion;
    if (expectedGameVersion !== undefined) this.expectedGameVersion = expectedGameVersion;
  }
}

export const protocolError = (message, status = null) => new BattleHexesApiError({
  status,
  code: 'protocolError',
  message,
});
