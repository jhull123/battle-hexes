const toCoordKey = (hex) => `${hex.row},${hex.column}`;

const fromCoordKey = (key) => {
  const [row, column] = key.split(',').map(Number);
  return { row, column };
};

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

const addNeighbor = (neighborsByHexKey, fromHex, toHex) => {
  const fromKey = toCoordKey(fromHex);
  const toKey = toCoordKey(toHex);

  if (!neighborsByHexKey.has(fromKey)) {
    neighborsByHexKey.set(fromKey, new Set());
  }

  neighborsByHexKey.get(fromKey).add(toKey);
};

export const buildRoadGraph = (roads) => {
  const neighborsByHexKey = new Map();

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
      if (startKey === endKey) {
        continue;
      }

      addNeighbor(neighborsByHexKey, start, end);
      addNeighbor(neighborsByHexKey, end, start);
    }
  }

  const degreesByHexKey = new Map();
  for (const [hexKey, neighbors] of neighborsByHexKey.entries()) {
    degreesByHexKey.set(hexKey, neighbors.size);
  }

  return { neighborsByHexKey, degreesByHexKey };
};

export const getJunctionHexKeys = (roads) => {
  const { degreesByHexKey } = buildRoadGraph(roads);
  const junctionHexKeys = new Set();

  for (const [hexKey, degree] of degreesByHexKey.entries()) {
    if (degree >= 3) {
      junctionHexKeys.add(hexKey);
    }
  }

  return junctionHexKeys;
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
    const radius = this.#hexDrawer.getHexRadius();

    this.#drawRoadPolylines(roads, radius);
    this.#drawJunctionHubs(getJunctionHexKeys(roads), radius);
  }

  #drawRoadPolylines(roads, radius) {
    const ctx = this.#p.drawingContext;

    this.#p.push();
    this.#p.noFill();
    this.#p.strokeCap(this.#p.ROUND);
    this.#p.strokeJoin(this.#p.ROUND);

    ctx.shadowBlur = radius * 0.12;
    ctx.shadowColor = 'rgba(0,0,0,0.18)';
    this.#p.stroke(0x8A, 0x76, 0x50, 220);
    this.#p.strokeWeight(radius * 0.33);
    this.#drawRoadLinePass(roads);

    ctx.shadowBlur = 0;
    ctx.shadowColor = 'rgba(0,0,0,0)';
    this.#p.stroke(0xC7, 0xB4, 0x8A, 205);
    this.#p.strokeWeight(radius * 0.18);
    this.#drawRoadLinePass(roads);

    this.#p.pop();
  }

  #drawRoadLinePass(roads) {
    for (const road of roads) {
      const points = getRoadPoints(road)
        .map((point) => normalizePathPoint(point))
        .filter((point) => point !== undefined)
        .map((point) => this.#hexDrawer.hexCenter(point));

      if (points.length < 2) {
        continue;
      }

      this.#p.beginShape();
      for (const point of points) {
        this.#p.vertex(point.x, point.y);
      }
      this.#p.endShape();
    }
  }

  #drawJunctionHubs(junctionHexKeys, radius) {
    if (junctionHexKeys.size === 0) {
      return;
    }

    this.#p.push();
    this.#p.noStroke();

    for (const hexKey of junctionHexKeys) {
      const center = this.#hexDrawer.hexCenter(fromCoordKey(hexKey));

      this.#p.fill(0x8A, 0x76, 0x50, 190);
      this.#p.circle(center.x, center.y, radius * 0.22);

      this.#p.fill(0xC7, 0xB4, 0x8A, 195);
      this.#p.circle(center.x, center.y, radius * 0.12);
    }

    this.#p.pop();
  }
}
