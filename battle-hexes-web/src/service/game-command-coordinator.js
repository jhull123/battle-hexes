export class GameCommandCoordinator {
  #tails = new Map();

  enqueue(gameId, command) {
    const previous = this.#tails.get(gameId) ?? Promise.resolve();
    const result = previous.catch(() => {}).then(command);
    const tail = result.then(() => {}, () => {}).finally(() => {
      if (this.#tails.get(gameId) === tail) this.#tails.delete(gameId);
    });
    this.#tails.set(gameId, tail);
    return result;
  }
}
