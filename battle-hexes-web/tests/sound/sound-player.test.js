import { SoundPlayer } from '../../src/sound/sound-player.js';

describe('SoundPlayer', () => {
  const buildGame = (factionId = 'axis') => ({
    getBoard: () => ({
      getUnits: () => [{
        getId: () => 'firing-unit',
        getFaction: () => ({
          getId: () => factionId,
        }),
      }],
    }),
  });

  test('plays effect outcome sound for firing faction', async () => {
    const play = jest.fn(() => Promise.resolve());
    const soundPlayer = new SoundPlayer({
      audioFactory: () => ({ play }),
    });

    soundPlayer.playDefensiveFireEvents({
      events: [{
        firing_unit_id: 'firing-unit',
        outcome: 'retreat',
      }],
      game: buildGame('axis'),
      scenario: {
        factions: [{
          id: 'axis',
          sounds: {
            defensive_fire: {
              effect: 'axis-effect.ogg',
            },
          },
        }],
      },
    });

    expect(play).toHaveBeenCalledTimes(1);
  });

  test('plays no_effect outcome sound for firing faction', async () => {
    const play = jest.fn(() => Promise.resolve());
    const soundPlayer = new SoundPlayer({
      audioFactory: (path) => ({
        play,
        path,
      }),
    });

    soundPlayer.playDefensiveFireEvents({
      events: [{
        firing_unit_id: 'firing-unit',
        outcome: 'no_effect',
      }],
      game: buildGame('axis'),
      scenario: {
        factions: [{
          id: 'axis',
          sounds: {
            defensive_fire: {
              no_effect: 'axis-no-effect.ogg',
            },
          },
        }],
      },
    });

    expect(play).toHaveBeenCalledTimes(1);
  });

  test('does not play when defensive fire sound config is missing, missing key, or empty', () => {
    const play = jest.fn(() => Promise.resolve());
    const soundPlayer = new SoundPlayer({
      audioFactory: () => ({ play }),
    });

    soundPlayer.playDefensiveFireEvents({
      events: [{ firing_unit_id: 'firing-unit', outcome: 'retreat' }],
      game: buildGame('axis'),
      scenario: {
        factions: [{ id: 'axis', sounds: {} }],
      },
    });

    soundPlayer.playDefensiveFireEvents({
      events: [{ firing_unit_id: 'firing-unit', outcome: 'retreat' }],
      game: buildGame('axis'),
      scenario: {
        factions: [{
          id: 'axis',
          sounds: {
            defensive_fire: {
              no_effect: 'axis-no-effect.ogg',
            },
          },
        }],
      },
    });

    soundPlayer.playDefensiveFireEvents({
      events: [{ firing_unit_id: 'firing-unit', outcome: 'retreat' }],
      game: buildGame('axis'),
      scenario: {
        factions: [{
          id: 'axis',
          sounds: {
            defensive_fire: {
              effect: '',
            },
          },
        }],
      },
    });

    expect(play).not.toHaveBeenCalled();
  });

  test('uses firing faction-specific sound mapping', () => {
    const requestedPaths = [];
    const soundPlayer = new SoundPlayer({
      audioFactory: (soundPath) => {
        requestedPaths.push(soundPath);
        return { play: () => Promise.resolve() };
      },
    });

    soundPlayer.playDefensiveFireEvents({
      events: [{
        firing_unit_id: 'firing-unit',
        outcome: 'retreat',
      }],
      game: buildGame('allies'),
      scenario: {
        factions: [{
          id: 'axis',
          sounds: {
            defensive_fire: {
              effect: 'axis-effect.ogg',
            },
          },
        }, {
          id: 'allies',
          sounds: {
            defensive_fire: {
              effect: 'allies-effect.ogg',
            },
          },
        }],
      },
    });

    expect(requestedPaths).toEqual(['/sounds/allies-effect.ogg']);
  });

  test('logs warning and continues processing when playback fails', async () => {
    const logger = { warn: jest.fn() };
    const soundPlayer = new SoundPlayer({
      audioFactory: () => ({
        play: jest.fn(() => Promise.reject(new Error('decode failed'))),
      }),
      logger,
    });

    soundPlayer.playDefensiveFireEvents({
      events: [
        { firing_unit_id: 'firing-unit', outcome: 'retreat' },
        { firing_unit_id: 'firing-unit', outcome: 'retreat' },
      ],
      game: buildGame('axis'),
      scenario: {
        factions: [{
          id: 'axis',
          sounds: {
            defensive_fire: {
              effect: 'axis-effect.ogg',
            },
          },
        }],
      },
    });

    await Promise.resolve();
    await Promise.resolve();

    expect(logger.warn).toHaveBeenCalled();
  });

  test('resolves generic faction sound path from nested keys', () => {
    const soundPlayer = new SoundPlayer();
    const path = soundPlayer.getFactionSoundPath({
      scenario: {
        factions: [{
          id: 'axis',
          sounds: {
            ui: {
              click: 'button-click.ogg',
            },
          },
        }],
      },
      factionId: 'axis',
      soundPath: ['ui', 'click'],
    });

    expect(path).toBe('/sounds/button-click.ogg');
  });
});
