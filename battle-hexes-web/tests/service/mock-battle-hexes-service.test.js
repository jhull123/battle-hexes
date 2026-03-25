import fs from 'node:fs';
import path from 'node:path';
import { MockBattleHexesService } from '../../src/service/mock-battle-hexes-service.js';

describe('MockBattleHexesService', () => {
  test('getGame returns the get-game mock response payload', async () => {
    const service = new MockBattleHexesService();
    const expectedPayload = JSON.parse(
      fs.readFileSync(
        path.resolve('src/service/mock-responses/get-game.json'),
        'utf8',
      ),
    );

    const response = await service.getGame('ignored-id');

    expect(response).toEqual(expectedPayload);
  });

  test('getGame returns a deep clone of the mock payload', async () => {
    const service = new MockBattleHexesService();

    const firstResponse = await service.getGame('ignored-id');
    firstResponse.board.units[0].name = 'changed';

    const secondResponse = await service.getGame('ignored-id');

    expect(secondResponse.board.units[0].name).not.toBe('changed');
  });
});
