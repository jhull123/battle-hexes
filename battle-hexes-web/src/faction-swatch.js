const DEFAULT_SWATCH_COLOR = '#b0b0b0';

export function createFactionSwatch(faction, ...classNames) {
  const swatch = document.createElement('span');
  swatch.classList.add('victory-swatch', ...classNames);
  swatch.style.backgroundColor = faction?.getCounterColor?.() ?? DEFAULT_SWATCH_COLOR;
  swatch.setAttribute('role', 'img');
  swatch.setAttribute('aria-label', faction ? `${faction.getName()} faction` : 'Unknown faction');
  return swatch;
}

export function createPlayerSwatch(player, ...classNames) {
  const swatch = document.createElement('span');
  swatch.classList.add('victory-swatch', ...classNames);
  swatch.style.backgroundColor = getPlayerSwatchColor(player);
  swatch.setAttribute('role', 'img');
  swatch.setAttribute('aria-label', player ? `${player.getName()} player` : 'Unknown player');
  return swatch;
}

export function getPlayerSwatchColor(player) {
  const color = player?.getFactions?.()[0]?.getCounterColor?.();
  return typeof color === 'string' && color.trim().length > 0
    ? color
    : DEFAULT_SWATCH_COLOR;
}
