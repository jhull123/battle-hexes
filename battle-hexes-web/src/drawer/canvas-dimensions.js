export function getBoardPixelWidth(columns, hexRadius) {
  if (!Number.isFinite(columns) || columns <= 0) {
    return 0;
  }

  return (2 * hexRadius) + (columns - 1) * (hexRadius * 1.5);
}

export function getBoardPixelHeight(rows, columns, hexRadius) {
  if (!Number.isFinite(rows) || rows <= 0) {
    return 0;
  }

  const hexHeight = Math.sqrt(3) * hexRadius;
  const hasOddColumns = Number.isFinite(columns) && columns > 1;
  const oddColumnBottomOffset = hasOddColumns ? hexHeight / 2 : 0;
  const topVertexOffset = hexRadius - (hexHeight / 2);

  return (rows * hexHeight) + oddColumnBottomOffset + topVertexOffset;
}

export function getCanvasDimensions({
  rows,
  columns,
  hexRadius,
  windowWidth,
  menuWidth,
  canvasMargin,
}) {
  const boardWidth = getBoardPixelWidth(columns, hexRadius);
  const boardHeight = getBoardPixelHeight(rows, columns, hexRadius);
  const availableWidth = windowWidth - menuWidth - canvasMargin;

  return {
    width: Math.ceil(Math.max(boardWidth, availableWidth)),
    height: Math.ceil(boardHeight),
  };
}
