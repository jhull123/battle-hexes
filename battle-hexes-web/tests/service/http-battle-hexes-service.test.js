import { HttpBattleHexesService } from '../../src/service/http-battle-hexes-service.js';

describe('HttpBattleHexesService server response logging', () => {
  test('logs server response when logServerResponses is enabled', async () => {
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'scenario-1', name: 'Scenario 1' }),
    });
    const consoleInfoSpy = jest.spyOn(console, 'info').mockImplementation(() => {});

    const service = new HttpBattleHexesService({
      apiBaseUrl: 'http://localhost:8000',
      fetchImpl,
      logServerResponses: true,
    });

    await service.listScenarios();

    expect(consoleInfoSpy).toHaveBeenCalledWith(
      'server response for listScenarios: {"id":"scenario-1","name":"Scenario 1"}',
    );

    consoleInfoSpy.mockRestore();
  });

  test('does not log server response when logServerResponses is disabled', async () => {
    const fetchImpl = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'scenario-1', name: 'Scenario 1' }),
    });
    const consoleInfoSpy = jest.spyOn(console, 'info').mockImplementation(() => {});

    const service = new HttpBattleHexesService({
      apiBaseUrl: 'http://localhost:8000',
      fetchImpl,
      logServerResponses: false,
    });

    await service.listScenarios();

    expect(consoleInfoSpy).not.toHaveBeenCalled();

    consoleInfoSpy.mockRestore();
  });
});
