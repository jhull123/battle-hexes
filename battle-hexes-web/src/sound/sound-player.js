const NO_EFFECT_OUTCOME = 'no_effect';

export class SoundPlayer {
  #audioFactory;
  #logger;

  constructor({
    audioFactory = (soundPath) => new Audio(soundPath),
    logger = console,
  } = {}) {
    this.#audioFactory = audioFactory;
    this.#logger = logger;
  }

  getFactionSoundPath({ scenario, factionId, soundPath }) {
    if (!scenario || !factionId || !Array.isArray(soundPath) || soundPath.length === 0) {
      return null;
    }

    const factions = Array.isArray(scenario.factions) ? scenario.factions : [];
    const faction = factions.find((entry) => entry.id === factionId);
    if (!faction) {
      return null;
    }

    let soundFilename = faction.sounds;
    for (const segment of soundPath) {
      soundFilename = soundFilename?.[segment];
    }
    if (typeof soundFilename !== 'string' || soundFilename.trim().length === 0) {
      return null;
    }

    return `/sounds/${soundFilename}`;
  }

  playSound(soundPath) {
    const audio = this.#audioFactory(soundPath);
    return audio.play();
  }

  playDefensiveFireEvents({ events, game, scenario }) {
    if (!Array.isArray(events) || events.length === 0) {
      return;
    }

    for (const event of events) {
      const factionId = this.#resolveFiringFactionId(game, event?.firing_unit_id);
      const outcomeKey = event?.outcome === NO_EFFECT_OUTCOME ? 'no_effect' : 'effect';
      const soundPath = this.getFactionSoundPath({
        scenario,
        factionId,
        soundPath: ['defensive_fire', outcomeKey],
      });
      if (!soundPath) {
        continue;
      }

      this.playSound(soundPath).catch((error) => {
        this.#logger.warn('Failed to play defensive fire sound', error);
      });
    }
  }

  #resolveFiringFactionId(game, firingUnitId) {
    if (!game || !firingUnitId) {
      return null;
    }

    const units = game.getBoard?.().getUnits?.() ?? [];
    for (const unit of units) {
      if (unit.getId?.() === firingUnitId) {
        return unit.getFaction?.().getId?.() ?? null;
      }
    }

    return null;
  }
}
