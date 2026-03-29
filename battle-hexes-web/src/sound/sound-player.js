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

    this.#logger.info("===== SCENARIO =====");
    this.#logger.info(JSON.stringify(scenario));

    const factions = Array.isArray(scenario.factions) ? scenario.factions : [];
    this.#logger.info("Found " + factions.length + " factions.");
    const faction = factions.find((entry) => entry.id === factionId);
    if (!faction) {
      this.#logger.warn("Did not find faction with factionId=" + factionId);
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
    this.#logger.info("Playing defensive fire sound fx for " + events.length + " events.");
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
      this.#logger.info(
        "firing_unit_id=" + event?.firing_unit_id +
        ", factionId=" + factionId + ", outcomeKey=" + outcomeKey +
        ", soundPath=" + soundPath
      );
      if (!soundPath) {
        this.#logger.warn(
          "No defensive fire sound found for factionId=" + factionId +
          " and outcomeKey=" + outcomeKey
        );
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
