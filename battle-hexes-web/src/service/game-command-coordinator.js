// Serializes commands per game and can wait for each response to be applied before continuing.
export class GameCommandCoordinator {
  #tails = new Map();
  #applicationAcknowledgements = new Map();

  enqueue(gameId, command, { awaitResponseApplication = false } = {}) {
    const previous = this.#tails.get(gameId) ?? Promise.resolve();
    const result = previous.catch(() => {}).then(command);
    const acknowledgement = awaitResponseApplication ? this.#newAcknowledgement(gameId) : null;
    result.catch(() => this.#removeAcknowledgement(gameId, acknowledgement));
    const tail = result.then(() => acknowledgement?.promise, () => {}).finally(() => {
      if (this.#tails.get(gameId) === tail) this.#tails.delete(gameId);
    });
    this.#tails.set(gameId, tail);
    return result;
  }

  acknowledgeResponseApplication(gameId) {
    const acknowledgements = this.#applicationAcknowledgements.get(gameId);
    const acknowledgement = acknowledgements?.shift();
    if (acknowledgements?.length === 0) this.#applicationAcknowledgements.delete(gameId);
    acknowledgement?.resolve();
  }

  #newAcknowledgement(gameId) {
    let resolve;
    const acknowledgement = { promise: new Promise((callback) => { resolve = callback; }) };
    acknowledgement.resolve = resolve;
    const acknowledgements = this.#applicationAcknowledgements.get(gameId) ?? [];
    acknowledgements.push(acknowledgement);
    this.#applicationAcknowledgements.set(gameId, acknowledgements);
    return acknowledgement;
  }

  #removeAcknowledgement(gameId, acknowledgement) {
    if (!acknowledgement) return;
    const acknowledgements = this.#applicationAcknowledgements.get(gameId);
    const index = acknowledgements?.indexOf(acknowledgement) ?? -1;
    if (index < 0) return;
    acknowledgements.splice(index, 1);
    if (acknowledgements.length === 0) this.#applicationAcknowledgements.delete(gameId);
  }
}
