const RESULT_LABELS = {
  noEffect: 'No effect',
  retreated: 'Target retreated',
  eliminated: 'Target eliminated',
};

export class DefensiveFireEventRenderer {
  render(event) {
    const entry = document.createElement('div');
    entry.className = 'game-log-defensive-fire';

    const heading = document.createElement('strong');
    heading.textContent = 'Defensive Fire';
    entry.append(
      heading,
      this.#line('Firing unit', event.firingUnit.name),
      this.#line('Target unit', event.targetUnit.name),
      this.#line('Success probability', `${(event.successProbability * 100).toFixed(2)}%`),
      this.#line('Random roll', event.randomRoll.toFixed(2)),
      this.#line('Result', RESULT_LABELS[event.outcome]),
    );
    const summary = document.createElement('div');
    summary.className = 'game-log-defensive-fire-summary';
    summary.textContent = event.summary;
    entry.appendChild(summary);
    return entry;
  }

  #line(label, value) {
    const line = document.createElement('div');
    line.textContent = `${label}: ${value}`;
    return line;
  }
}
