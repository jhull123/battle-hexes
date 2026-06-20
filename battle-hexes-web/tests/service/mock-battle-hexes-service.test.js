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

describe('mock API payload casing', () => {
  const mockResponseDirectory = path.resolve('src/service/mock-responses');
  const snakeCaseKeyPattern = /^[a-z][a-z0-9]*(_[a-z0-9]+)+$/;

  function collectSnakeCaseKeys(value, pathSegments = []) {
    if (Array.isArray(value)) {
      return value.flatMap((item, index) => collectSnakeCaseKeys(item, [...pathSegments, `[${index}]`]));
    }

    if (!value || typeof value !== 'object') {
      return [];
    }

    return Object.entries(value).flatMap(([key, nestedValue]) => {
      const currentPath = [...pathSegments, key];
      const matches = snakeCaseKeyPattern.test(key) ? [currentPath.join('.')] : [];
      return [...matches, ...collectSnakeCaseKeys(nestedValue, currentPath)];
    });
  }

  test('uses camelCase keys in frontend mock API responses', () => {
    const mockResponseFiles = fs
      .readdirSync(mockResponseDirectory)
      .filter((fileName) => fileName.endsWith('.json'));

    const snakeCaseKeys = mockResponseFiles.flatMap((fileName) => {
      const payload = JSON.parse(
        fs.readFileSync(path.join(mockResponseDirectory, fileName), 'utf8'),
      );
      return collectSnakeCaseKeys(payload).map((keyPath) => `${fileName}:${keyPath}`);
    });

    expect(snakeCaseKeys).toEqual([]);
  });
});
