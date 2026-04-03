import { SoundPlayer } from '../src/sound-player.js';
import { Faction } from '../src/model/faction.js';

const createAudioFactory = (playImpl = () => Promise.resolve()) => {
  const factory = jest.fn(() => ({
    play: jest.fn(playImpl),
  }));
  return factory;
};

describe('SoundPlayer defensive fire playback', () => {
  test('plays effect sound from the firing unit faction for non-no_effect outcomes', async () => {
    const faction = new Faction('red', 'Red', '#f00', {
      defensive_fire: {
        effect: 'm1_single_rifle_shot.ogg',
      },
    });
    const game = {
      getFactionForUnitId: jest.fn(() => faction),
    };
    const audioFactory = createAudioFactory();

    const soundPlayer = new SoundPlayer(game, { audioFactory });
    await soundPlayer.playDefensiveFireEvents([{ firing_unit_id: 'unit-1', outcome: 'retreat' }]);

    expect(game.getFactionForUnitId).toHaveBeenCalledWith('unit-1');
    expect(audioFactory).toHaveBeenCalledWith('/sounds/m1_single_rifle_shot.ogg');
  });

  test('plays no_effect sound for no_effect outcomes', async () => {
    const faction = new Faction('red', 'Red', '#f00', {
      defensive_fire: {
        no_effect: 'k98_distant.ogg',
      },
    });
    const game = {
      getFactionForUnitId: jest.fn(() => faction),
    };
    const audioFactory = createAudioFactory();

    const soundPlayer = new SoundPlayer(game, { audioFactory });
    await soundPlayer.playDefensiveFireEvents([{ firing_unit_id: 'unit-1', outcome: 'no_effect' }]);

    expect(audioFactory).toHaveBeenCalledWith('/sounds/k98_distant.ogg');
  });

  test('stays silent for missing defensive fire config or empty filename', async () => {
    const faction = new Faction('red', 'Red', '#f00', {
      defensive_fire: {
        effect: '',
      },
    });
    const game = {
      getFactionForUnitId: jest.fn(() => faction),
    };
    const audioFactory = createAudioFactory();

    const soundPlayer = new SoundPlayer(game, { audioFactory });
    await soundPlayer.playDefensiveFireEvents([
      { firing_unit_id: 'unit-1', outcome: 'retreat' },
      { firing_unit_id: 'unit-2', outcome: 'no_effect' },
    ]);

    expect(audioFactory).not.toHaveBeenCalled();
  });

  test('uses each firing unit faction mapping independently', async () => {
    const redFaction = new Faction('red', 'Red', '#f00', {
      defensive_fire: { effect: 'red_effect.ogg' },
    });
    const blueFaction = new Faction('blue', 'Blue', '#00f', {
      defensive_fire: { effect: 'blue_effect.ogg' },
    });
    const game = {
      getFactionForUnitId: jest.fn((unitId) => (unitId === 'red-unit' ? redFaction : blueFaction)),
    };
    const audioFactory = createAudioFactory();

    const soundPlayer = new SoundPlayer(game, { audioFactory });
    await soundPlayer.playDefensiveFireEvents([
      { firing_unit_id: 'red-unit', outcome: 'retreat' },
      { firing_unit_id: 'blue-unit', outcome: 'retreat' },
    ]);

    expect(audioFactory).toHaveBeenNthCalledWith(1, '/sounds/red_effect.ogg');
    expect(audioFactory).toHaveBeenNthCalledWith(2, '/sounds/blue_effect.ogg');
  });

  test('logs warning and continues when playback fails', async () => {
    const faction = new Faction('red', 'Red', '#f00', {
      defensive_fire: {
        effect: 'red_effect.ogg',
      },
    });
    const game = {
      getFactionForUnitId: jest.fn(() => faction),
    };
    const error = new Error('audio failed');
    const audioFactory = createAudioFactory(() => Promise.reject(error));
    const logger = { warn: jest.fn() };

    const soundPlayer = new SoundPlayer(game, { audioFactory, logger });
    await expect(soundPlayer.playDefensiveFireEvents([
      { firing_unit_id: 'unit-1', outcome: 'retreat' },
      { firing_unit_id: 'unit-1', outcome: 'retreat' },
    ])).resolves.toBeUndefined();

    expect(logger.warn).toHaveBeenCalledTimes(2);
    expect(audioFactory).toHaveBeenCalledTimes(2);
  });
});
