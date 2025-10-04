import { HexDrawer } from '../drawer/hex-drawer.js';

export const DEFAULT_SCROLL_SPEED = 22;

const SCROLL_DIRECTION = normalizeDirection({ x: 1, y: 0.32 });
const GRID_BUFFER = 3;
const STROKE_COLOR = 'rgba(132, 173, 218, 0.22)';
const STROKE_WEIGHT = 1.5;
const FILL_COLOR = 'rgba(24, 39, 58, 0.55)';

export class ScrollingHexLandscape {
  #p;
  #hexDrawer;
  #hexRadius;
  #hexHeight;
  #hexDiameter;
  #horizontalSpacing;
  #scrollSpeed;
  #totalScrollX;
  #totalScrollY;
  #baseColumnOffset;
  #baseRowOffset;
  #visibleColumnCount;
  #visibleRowCount;

  constructor(p, { hexRadius = 64, scrollSpeed = DEFAULT_SCROLL_SPEED, hexDrawer } = {}) {
    this.#p = p;
    this.#hexRadius = hexRadius;
    this.#hexHeight = Math.sqrt(3) * hexRadius;
    this.#hexDiameter = hexRadius * 2;
    this.#horizontalSpacing = this.#hexDiameter - (this.#hexRadius / 2);
    this.#hexDrawer = hexDrawer ?? new HexDrawer(p, hexRadius);
    if (typeof this.#hexDrawer.setShowHexCoords === 'function') {
      this.#hexDrawer.setShowHexCoords(false);
    }
    this.#scrollSpeed = scrollSpeed;
    this.#totalScrollX = 0;
    this.#totalScrollY = 0;
    this.#baseColumnOffset = 0;
    this.#baseRowOffset = 0;
    this.#visibleColumnCount = 0;
    this.#visibleRowCount = 0;
  }

  setScrollSpeed(speed) {
    this.#scrollSpeed = speed;
  }

  getScrollSpeed() {
    return this.#scrollSpeed;
  }

  resize(width, height) {
    this.#visibleColumnCount = Math.ceil((width + this.#horizontalSpacing) / this.#horizontalSpacing);
    this.#visibleRowCount = Math.ceil((height + this.#hexHeight) / this.#hexHeight);
  }

  getVisibleGridSize() {
    return {
      rows: this.#visibleRowCount,
      columns: this.#visibleColumnCount,
    };
  }

  draw(deltaTimeMs) {
    if (!this.#visibleColumnCount || !this.#visibleRowCount) {
      return;
    }

    const deltaSeconds = (Number.isFinite(deltaTimeMs) ? deltaTimeMs : 16.67) / 1000;
    const deltaX = SCROLL_DIRECTION.x * this.#scrollSpeed * deltaSeconds;
    const deltaY = SCROLL_DIRECTION.y * this.#scrollSpeed * deltaSeconds;

    this.#totalScrollX += deltaX;
    this.#totalScrollY += deltaY;

    if (this.#totalScrollX >= Number.MAX_SAFE_INTEGER / 2) {
      this.#totalScrollX = 0;
    }
    if (this.#totalScrollY >= Number.MAX_SAFE_INTEGER / 2) {
      this.#totalScrollY = 0;
    }

    this.#baseColumnOffset = Math.floor(this.#totalScrollX / this.#horizontalSpacing);
    this.#baseRowOffset = Math.floor(this.#totalScrollY / this.#hexHeight);

    const fractionalOffsetX = this.#totalScrollX - this.#baseColumnOffset * this.#horizontalSpacing;
    const fractionalOffsetY = this.#totalScrollY - this.#baseRowOffset * this.#hexHeight;

    const startColumn = this.#baseColumnOffset - GRID_BUFFER;
    const endColumn = startColumn + this.#visibleColumnCount + GRID_BUFFER * 2;
    const startRow = this.#baseRowOffset - GRID_BUFFER;
    const endRow = startRow + this.#visibleRowCount + GRID_BUFFER * 2;

    this.#p.push();
    this.#p.translate(-fractionalOffsetX, -fractionalOffsetY);

    for (let column = startColumn; column < endColumn; column++) {
      for (let row = startRow; row < endRow; row++) {
        this.#hexDrawer.drawHex({ row, column }, STROKE_COLOR, STROKE_WEIGHT, FILL_COLOR);
      }
    }

    this.#p.pop();
  }
}

function normalizeDirection(direction) {
  const magnitude = Math.hypot(direction.x, direction.y) || 1;
  return {
    x: direction.x / magnitude,
    y: direction.y / magnitude,
  };
}
