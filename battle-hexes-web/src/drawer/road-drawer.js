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
    const radius = this.#hexDrawer.getHexRadius();
    const graph = this.#buildRoadGraph(this.#getRoads());

    this.#drawRoadSegments(graph, radius);
    this.#drawRoadJunctions(graph, radius);
  }

  #buildRoadGraph(roads) {
    const nodes = new Map();
    const edgeSet = new Set();
    const edges = [];

    const getNode = (row, column) => {
      const key = `${row},${column}`;
      if (!nodes.has(key)) {
        nodes.set(key, {
          key,
          row,
          column,
          center: this.#hexDrawer.hexCenter({ row, column }),
          neighbors: new Set(),
        });
      }

      return nodes.get(key);
    };

    for (const road of roads) {
      for (const [row, column] of road.path) {
        getNode(row, column);
      }

      for (let index = 0; index < road.path.length - 1; index += 1) {
        const [fromRow, fromColumn] = road.path[index];
        const [toRow, toColumn] = road.path[index + 1];
        const fromNode = getNode(fromRow, fromColumn);
        const toNode = getNode(toRow, toColumn);

        if (fromNode.key === toNode.key) {
          continue;
        }

        const edgeKey = [fromNode.key, toNode.key].sort().join('|');
        if (edgeSet.has(edgeKey)) {
          continue;
        }

        edgeSet.add(edgeKey);
        fromNode.neighbors.add(toNode.key);
        toNode.neighbors.add(fromNode.key);
        edges.push({ from: fromNode.key, to: toNode.key });
      }
    }

    return { nodes, edges };
  }

  #drawRoadSegments(graph, radius) {
    if (graph.edges.length === 0) {
      return;
    }

    const ctx = this.#p.drawingContext;
    const drawEdgePass = () => {
      for (const edge of graph.edges) {
        const fromNode = graph.nodes.get(edge.from);
        const toNode = graph.nodes.get(edge.to);
        const segment = this.#trimmedSegment(fromNode, toNode, radius);
        this.#p.line(segment.start.x, segment.start.y, segment.end.x, segment.end.y);
      }
    };

    this.#p.push();
    this.#p.noFill();
    this.#p.strokeCap(this.#p.ROUND);
    this.#p.strokeJoin(this.#p.ROUND);

    ctx.shadowBlur = radius * 0.12;
    ctx.shadowColor = 'rgba(0,0,0,0.18)';
    this.#p.stroke(0x8A, 0x76, 0x50, 220);
    this.#p.strokeWeight(radius * 0.33);
    drawEdgePass();

    ctx.shadowBlur = 0;
    ctx.shadowColor = 'rgba(0,0,0,0)';
    this.#p.stroke(0xC7, 0xB4, 0x8A, 205);
    this.#p.strokeWeight(radius * 0.18);
    drawEdgePass();
    this.#p.pop();
  }

  #drawRoadJunctions(graph, radius) {
    const junctions = [...graph.nodes.values()].filter(
      (node) => node.neighbors.size >= 3
    );

    if (junctions.length === 0) {
      return;
    }

    this.#p.push();
    this.#p.noStroke();
    this.#p.fill(0x8A, 0x76, 0x50, 220);
    for (const junction of junctions) {
      this.#p.circle(junction.center.x, junction.center.y, radius * 0.24);
    }

    this.#p.fill(0xC7, 0xB4, 0x8A, 205);
    for (const junction of junctions) {
      this.#p.circle(junction.center.x, junction.center.y, radius * 0.14);
    }
    this.#p.pop();
  }

  #trimmedSegment(fromNode, toNode, radius) {
    const trimAmount = radius * 0.12;
    const direction = {
      x: toNode.center.x - fromNode.center.x,
      y: toNode.center.y - fromNode.center.y,
    };
    const length = Math.hypot(direction.x, direction.y);

    if (length === 0) {
      return { start: fromNode.center, end: toNode.center };
    }

    const startTrim = fromNode.neighbors.size >= 2 ? trimAmount : 0;
    const endTrim = toNode.neighbors.size >= 2 ? trimAmount : 0;
    let startRatio = startTrim / length;
    let endRatio = endTrim / length;

    if (startRatio + endRatio >= 1) {
      const safeScale = 0.95 / (startRatio + endRatio);
      startRatio *= safeScale;
      endRatio *= safeScale;
    }

    return {
      start: {
        x: fromNode.center.x + direction.x * startRatio,
        y: fromNode.center.y + direction.y * startRatio,
      },
      end: {
        x: toNode.center.x - direction.x * endRatio,
        y: toNode.center.y - direction.y * endRatio,
      },
    };
  }
}
