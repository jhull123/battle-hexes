const RESULT_LABELS = {
  noEffect: 'No Effect',
  retreated: 'Target Retreated',
  eliminated: 'Target Eliminated',
};

export class DefensiveFireEventRenderer {
  render(event) {
    const entry = document.createElement('details');
    entry.className = 'game-log-defensive-fire';

    const heading = document.createElement('summary');
    heading.className = 'game-log-defensive-fire-title';
    const disclosure = document.createElement('span');
    disclosure.className = 'game-log-disclosure';
    disclosure.setAttribute('aria-hidden', 'true');
    const title = document.createElement('span');
    title.textContent = `Defensive Fire - ${RESULT_LABELS[event.outcome]}`;
    heading.append(disclosure, title);
    entry.append(
      heading,
      this.#line('Firing unit', event.firingUnit.name),
      this.#line('Target unit', event.targetUnit.name),
      this.#line('Success probability', `${(event.successProbability * 100).toFixed(2)}%`),
      this.#line('Random roll', event.randomRoll.toFixed(2)),
    );
    return entry;
  }

  #line(label, value) {
    const line = document.createElement('div');
    line.textContent = `${label}: ${value}`;
    return line;
  }
}
