export class SoundPlayer {
  #game;
  #audioFactory;
  #logger;

  constructor(game, { audioFactory = (path) => new Audio(path), logger = console } = {}) {
    this.#game = game;
    this.#audioFactory = audioFactory;
    this.#logger = logger;
  }

  setGame(game) {
    this.#game = game;
  }

  async playDefensiveFireEvents(events = []) {
    if (!Array.isArray(events) || events.length === 0) {
      return;
    }

    for (const event of events) {
      await this.#playDefensiveFireEvent(event);
    }
  }

  async #playDefensiveFireEvent(event) {
    const soundFilename = this.#resolveDefensiveFireSoundFilename(event);
    if (!soundFilename) {
      return;
    }

    await this.#playSoundFile(soundFilename);
  }

  #resolveDefensiveFireSoundFilename(event) {
    const soundKey = event?.outcome === 'no_effect' ? 'no_effect' : 'effect';
    return this.#resolveFactionSoundForEvent(event, ['defensive_fire', soundKey]);
  }

  #resolveFactionSoundForEvent(event, soundPath) {
    const firingUnitId = event?.firing_unit_id;
    if (typeof firingUnitId !== 'string' || firingUnitId.length === 0) {
      return null;
    }

    const faction = this.#game.getFactionForUnitId?.(firingUnitId);
    if (!faction) {
      return null;
    }

    const soundValue = this.#readNestedPath(faction.getSounds?.(), soundPath);
    if (typeof soundValue !== 'string' || soundValue.trim().length === 0) {
      return null;
    }

    return soundValue;
  }

  #readNestedPath(source, path) {
    let value = source;
    for (const key of path) {
      if (!value || typeof value !== 'object') {
        return undefined;
      }
      value = value[key];
    }
    return value;
  }

  async #playSoundFile(filename) {
    const audioPath = `/sounds/${filename}`;

    try {
      const audio = this.#audioFactory(audioPath);
      await audio.play();
    } catch (error) {
      this.#logger.warn('Failed to play sound effect', { filename, error });
    }
  }
}
