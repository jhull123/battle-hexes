export function createFactionSwatch(faction, ...classNames) {
  const swatch = document.createElement('span');
  swatch.classList.add('victory-swatch', ...classNames);
  swatch.style.backgroundColor = faction?.getCounterColor?.() ?? '#b0b0b0';
  swatch.setAttribute('role', 'img');
  swatch.setAttribute('aria-label', faction ? `${faction.getName()} faction` : 'Unknown faction');
  return swatch;
}
