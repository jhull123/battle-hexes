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
    const paths = this.#buildDrawablePaths(graph);

    this.#drawRoadCurves(paths, graph, radius);
  }

  #buildRoadGraph(roads) {
    const nodes = new Map();
    const edgeSet = new Set();

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
      }
    }

    return { nodes, edgeSet };
  }

  #buildDrawablePaths(graph) {
    const unvisitedEdges = new Set(graph.edgeSet);
    const paths = [];

    const tryStartWalk = (startKey, neighborKey) => {
      const path = this.#walkPath(graph, unvisitedEdges, startKey, neighborKey);
      if (path.length >= 2) {
        paths.push(path);
      }
    };

    for (const node of graph.nodes.values()) {
      if (node.neighbors.size === 2) {
        continue;
      }

      for (const neighborKey of node.neighbors) {
        tryStartWalk(node.key, neighborKey);
      }
    }

    while (unvisitedEdges.size > 0) {
      const edgeKey = unvisitedEdges.values().next().value;
      const [fromKey, toKey] = edgeKey.split('|');
      tryStartWalk(fromKey, toKey);
    }

    return paths;
  }

  #walkPath(graph, unvisitedEdges, startKey, nextKey) {
    const path = [startKey];
    let previousKey = startKey;
    let currentKey = nextKey;

    if (!this.#markVisitedEdge(unvisitedEdges, startKey, nextKey)) {
      return path;
    }

    path.push(currentKey);

    while (true) {
      const currentNode = graph.nodes.get(currentKey);
      const candidates = [...currentNode.neighbors]
        .filter((neighborKey) => neighborKey !== previousKey)
        .filter((neighborKey) => this.#isEdgeUnvisited(unvisitedEdges, currentKey, neighborKey));

      if (candidates.length === 0) {
        break;
      }

      const nextCandidate = this.#pickNextNode(graph, previousKey, currentKey, candidates);
      if (!nextCandidate || !this.#markVisitedEdge(unvisitedEdges, currentKey, nextCandidate)) {
        break;
      }

      path.push(nextCandidate);
      previousKey = currentKey;
      currentKey = nextCandidate;
    }

    return path;
  }

  #pickNextNode(graph, previousKey, currentKey, candidates) {
    const currentNode = graph.nodes.get(currentKey);

    if (currentNode.neighbors.size === 2 && candidates.length > 0) {
      return candidates[0];
    }

    if (!previousKey) {
      return candidates[0] ?? null;
    }

    const previousNode = graph.nodes.get(previousKey);
    const inX = currentNode.center.x - previousNode.center.x;
    const inY = currentNode.center.y - previousNode.center.y;
    const inLength = Math.hypot(inX, inY) || 1;

    let bestKey = null;
    let bestScore = -Infinity;

    for (const candidateKey of candidates) {
      const candidateNode = graph.nodes.get(candidateKey);
      const outX = candidateNode.center.x - currentNode.center.x;
      const outY = candidateNode.center.y - currentNode.center.y;
      const outLength = Math.hypot(outX, outY) || 1;
      const score = (inX * outX + inY * outY) / (inLength * outLength);

      if (score > bestScore) {
        bestScore = score;
        bestKey = candidateKey;
      }
    }

    return bestScore > 0 ? bestKey : null;
  }

  #isEdgeUnvisited(unvisitedEdges, fromKey, toKey) {
    return unvisitedEdges.has(this.#edgeKey(fromKey, toKey));
  }

  #markVisitedEdge(unvisitedEdges, fromKey, toKey) {
    return unvisitedEdges.delete(this.#edgeKey(fromKey, toKey));
  }

  #edgeKey(fromKey, toKey) {
    return [fromKey, toKey].sort().join('|');
  }

  #drawRoadCurves(paths, graph, radius) {
    if (paths.length === 0) {
      return;
    }

    const ctx = this.#p.drawingContext;

    this.#p.push();
    this.#p.noFill();
    this.#p.strokeCap(this.#p.ROUND);
    this.#p.strokeJoin(this.#p.ROUND);

    ctx.shadowBlur = radius * 0.12;
    ctx.shadowColor = 'rgba(0,0,0,0.18)';
    this.#p.stroke(0x8A, 0x76, 0x50, 220);
    this.#p.strokeWeight(radius * 0.33);
    for (const path of paths) {
      this.#drawRoadCurve(path, graph, radius);
    }

    ctx.shadowBlur = 0;
    ctx.shadowColor = 'rgba(0,0,0,0)';
    this.#p.stroke(0xC7, 0xB4, 0x8A, 205);
    this.#p.strokeWeight(radius * 0.18);
    for (const path of paths) {
      this.#drawRoadCurve(path, graph, radius);
    }

    this.#p.pop();
  }

  #drawRoadCurve(pathKeys, graph, radius) {
    if (pathKeys.length < 2) {
      return;
    }

    const points = pathKeys.map((key) => graph.nodes.get(key).center);
    const trimmed = this.#trimCurveEndpoints(pathKeys, points, graph, radius);
    const first = trimmed[0];
    const last = trimmed[trimmed.length - 1];

    this.#p.beginShape();
    this.#p.curveVertex(first.x, first.y);
    this.#p.curveVertex(first.x, first.y);
    for (const point of trimmed) {
      this.#p.curveVertex(point.x, point.y);
    }
    this.#p.curveVertex(last.x, last.y);
    this.#p.curveVertex(last.x, last.y);
    this.#p.endShape();
  }

  #trimCurveEndpoints(pathKeys, points, graph, radius) {
    const trimmedPoints = points.map((point) => ({ x: point.x, y: point.y }));

    const trimEndpoint = (atStart) => {
      const nodeKey = atStart ? pathKeys[0] : pathKeys[pathKeys.length - 1];
      const nextIndex = atStart ? 1 : pathKeys.length - 2;
      const node = graph.nodes.get(nodeKey);

      if (node.neighbors.size < 3) {
        return;
      }

      const endpoint = atStart ? trimmedPoints[0] : trimmedPoints[trimmedPoints.length - 1];
      const adjacent = trimmedPoints[nextIndex];
      const dx = adjacent.x - endpoint.x;
      const dy = adjacent.y - endpoint.y;
      const distance = Math.hypot(dx, dy);
      if (distance === 0) {
        return;
      }

      const trim = Math.min(radius * 0.08, distance * 0.45);
      const ratio = trim / distance;
      endpoint.x += dx * ratio;
      endpoint.y += dy * ratio;
    };

    trimEndpoint(true);
    trimEndpoint(false);

    return trimmedPoints;
  }
}
