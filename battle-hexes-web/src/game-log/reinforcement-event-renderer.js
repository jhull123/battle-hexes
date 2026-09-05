export class ReinforcementEventRenderer {
  render(event) {
    const entry = document.createElement('div');
    const label = event.outcome === 'arrived' ? 'arrived' : 'blocked';
    const units = event.unitCount === 1 ? 'unit' : 'units';
    const [q, r] = event.entryCoordinate;
    entry.textContent = `Reinforcements ${label} - ${event.unitCount} ${units} at (${q}, ${r})`;
    return entry;
  }
}
