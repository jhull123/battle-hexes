export class TerrainHelper {
  #p;
  #hexDrawer;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
  }

  pickPosition(center, placementRadius, hexVertices, placedPoints, minDist) {
    const maxAttempts = 15;
    let fallbackCandidate;

    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const candidate = this.samplePointInHex(center, placementRadius, hexVertices);

      if (!fallbackCandidate) {
        fallbackCandidate = candidate;
      }

      const hasEnoughSpacing = placedPoints.every((point) => {
        const dx = candidate.x - point.x;
        const dy = candidate.y - point.y;
        return dx * dx + dy * dy >= minDist * minDist;
      });

      if (hasEnoughSpacing) {
        return candidate;
      }
    }

    return fallbackCandidate ?? center;
  }

  samplePointInHex(center, placementRadius, hexVertices) {
    const bounds = this.#boundsForVertices(hexVertices);
    const maxAttempts = 15;

    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const x = this.#p.random(bounds.minX, bounds.maxX);
      const y = this.#p.random(bounds.minY, bounds.maxY);

      if (this.#isPointInPolygon(x, y, hexVertices)) {
        return { x, y };
      }
    }

    const angle = this.#p.random(this.#p.TWO_PI);
    const distance = Math.sqrt(this.#p.random()) * placementRadius;
    return {
      x: center.x + this.#p.cos(angle) * distance,
      y: center.y + this.#p.sin(angle) * distance,
    };
  }

  getHexVertices(aHex, center, placementRadius) {
    const apiVertices = this.#hexDrawer.getHexVertices?.(aHex) ?? this.#hexDrawer.hexVertices?.(aHex);
    if (Array.isArray(apiVertices) && apiVertices.length >= 3) {
      return apiVertices;
    }

    const vertices = [];
    for (let i = 0; i < 6; i += 1) {
      const angle = this.#p.TWO_PI / 6 * i;
      vertices.push({
        x: center.x + this.#p.cos(angle) * placementRadius,
        y: center.y + this.#p.sin(angle) * placementRadius,
      });
    }
    return vertices;
  }

  #boundsForVertices(vertices) {
    return vertices.reduce((acc, vertex) => ({
      minX: Math.min(acc.minX, vertex.x),
      maxX: Math.max(acc.maxX, vertex.x),
      minY: Math.min(acc.minY, vertex.y),
      maxY: Math.max(acc.maxY, vertex.y),
    }), {
      minX: Number.POSITIVE_INFINITY,
      maxX: Number.NEGATIVE_INFINITY,
      minY: Number.POSITIVE_INFINITY,
      maxY: Number.NEGATIVE_INFINITY,
    });
  }

  #isPointInPolygon(x, y, polygon) {
    let inside = false;

    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i, i += 1) {
      const xi = polygon[i].x;
      const yi = polygon[i].y;
      const xj = polygon[j].x;
      const yj = polygon[j].y;

      const intersects = ((yi > y) !== (yj > y))
        && (x < ((xj - xi) * (y - yi)) / ((yj - yi) || Number.EPSILON) + xi);

      if (intersects) {
        inside = !inside;
      }
    }

    return inside;
  }
}
