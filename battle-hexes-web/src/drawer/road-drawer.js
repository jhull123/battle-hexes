const toCoordKey = (hex) => `${hex.row},${hex.column}`;

const normalizePathPoint = (point) => {
  if (Array.isArray(point)) {
    return { row: point[0], column: point[1] };
  }

  if (point && typeof point.row === 'number' && typeof point.column === 'number') {
    return { row: point.row, column: point.column };
  }

  return undefined;
};

const getRoadPoints = (road) => {
  if (Array.isArray(road.path)) {
    return road.path;
  }

  if (Array.isArray(road.segments)) {
    return road.segments;
  }

  return [];
};

export const getRoadConnectionsForHex = (roads, aHex) => {
  const aHexKey = toCoordKey(aHex);
  const neighborsByKey = new Map();

  for (const road of roads) {
    const points = getRoadPoints(road);
    for (let i = 0; i < points.length - 1; i += 1) {
      const start = normalizePathPoint(points[i]);
      const end = normalizePathPoint(points[i + 1]);

      if (!start || !end) {
        continue;
      }

      const startKey = toCoordKey(start);
      const endKey = toCoordKey(end);

      if (startKey === aHexKey && endKey !== aHexKey) {
        neighborsByKey.set(endKey, end);
      }

      if (endKey === aHexKey && startKey !== aHexKey) {
        neighborsByKey.set(startKey, start);
      }
    }
  }

  return [...neighborsByKey.values()];
};

export class RoadDrawer {
  #p;
  #hexDrawer;
  #getRoads;

  constructor(p, hexDrawer, getRoads) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
    this.#getRoads = getRoads;
  }

  draw() {
    this.drawAll();
  }

  drawAll() {
    const roads = this.#getRoads();
    const roadHexes = this.#getRoadHexes(roads);
    const radius = this.#hexDrawer.getHexRadius();

    for (const roadHex of roadHexes.values()) {
      const connections = getRoadConnectionsForHex(roads, roadHex);
      if (connections.length === 0) {
        continue;
      }

      this.#drawRoadJunction(roadHex, connections, radius);
    }
  }

  #getRoadHexes(roads) {
    const roadHexes = new Map();

    for (const road of roads) {
      const points = getRoadPoints(road);
      for (const point of points) {
        const normalized = normalizePathPoint(point);
        if (!normalized) {
          continue;
        }

        roadHexes.set(toCoordKey(normalized), normalized);
      }
    }

    return roadHexes;
  }

  #drawRoadJunction(roadHex, connectedNeighbors, radius) {
    const center = this.#hexDrawer.hexCenter(roadHex);
    const spokeLength = radius * 0.88;
    const hubRadius = radius * 0.16;
    const ctx = this.#p.drawingContext;

    this.#p.push();
    this.#p.noFill();
    this.#p.strokeCap(this.#p.ROUND);
    this.#p.strokeJoin(this.#p.ROUND);

    ctx.shadowBlur = radius * 0.12;
    ctx.shadowColor = 'rgba(0,0,0,0.18)';
    this.#p.stroke(0x8A, 0x76, 0x50, 220);
    this.#p.strokeWeight(radius * 0.33);
    this.#drawSpokes(center, connectedNeighbors, spokeLength);
    this.#drawHub(center, hubRadius);

    ctx.shadowBlur = 0;
    ctx.shadowColor = 'rgba(0,0,0,0)';
    this.#p.stroke(0xC7, 0xB4, 0x8A, 205);
    this.#p.strokeWeight(radius * 0.18);
    this.#drawSpokes(center, connectedNeighbors, spokeLength);
    this.#drawHub(center, hubRadius * 0.95);

    this.#p.pop();
  }

  #drawSpokes(center, connectedNeighbors, spokeLength) {
    for (const neighbor of connectedNeighbors) {
      const neighborCenter = this.#hexDrawer.hexCenter(neighbor);
      const dx = neighborCenter.x - center.x;
      const dy = neighborCenter.y - center.y;
      const magnitude = Math.hypot(dx, dy);

      if (magnitude === 0) {
        continue;
      }

      const endX = center.x + (dx / magnitude) * spokeLength;
      const endY = center.y + (dy / magnitude) * spokeLength;
      this.#p.line(center.x, center.y, endX, endY);
    }
  }

  #drawHub(center, hubRadius) {
    this.#p.circle(center.x, center.y, hubRadius * 2);
  }
}
