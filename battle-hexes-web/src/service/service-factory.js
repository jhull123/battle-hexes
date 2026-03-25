import { HttpBattleHexesService } from './http-battle-hexes-service.js';
import { MockBattleHexesService } from './mock-battle-hexes-service.js';

export const createBattleHexesService = ({
  mode = process.env.BATTLE_HEXES_SERVICE_MODE,
  apiBaseUrl = process.env.API_URL,
  fetchImpl = fetch,
} = {}) => {
  if (mode === 'mock') {
    console.info('BattleHexesService: using MockBattleHexesService because BATTLE_HEXES_SERVICE_MODE=mock.');
    return new MockBattleHexesService();
  }

  console.info(
    `BattleHexesService: using HttpBattleHexesService because BATTLE_HEXES_SERVICE_MODE=${mode ?? 'undefined'} (defaulting to http). API_URL=${apiBaseUrl}.`,
  );
  return new HttpBattleHexesService({ apiBaseUrl, fetchImpl });
};

export const battleHexesService = createBattleHexesService();
