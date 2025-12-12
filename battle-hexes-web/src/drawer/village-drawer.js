export class VillageDrawer {
  #p;
  #hexDrawer;

  constructor(p, hexDrawer) {
    this.#p = p;
    this.#hexDrawer = hexDrawer;
  }

  draw(aHex) {
    const strokeColor = '#2f3c2f';
    const fillColor = '#d6e7c7';

    this.#hexDrawer.drawHex(aHex, strokeColor, 2, fillColor);

    const center = this.#hexDrawer.hexCenter(aHex);
    const radius = this.#hexDrawer.getHexRadius();
    const buildingWidth = radius * 0.35;
    const buildingHeight = radius * 0.22;
    const clusterSpacing = radius * 0.12;
    const roofHeight = buildingHeight * 0.55;

    this.#p.rectMode(this.#p.CENTER);
    this.#p.stroke('#2b2926');
    this.#p.strokeWeight(2);
    this.#p.fill('#f3ecdd');

    const buildings = [
      { x: center.x - buildingWidth * 0.8, y: center.y + clusterSpacing * 0.2, w: buildingWidth, h: buildingHeight },
      { x: center.x + buildingWidth * 0.8, y: center.y + clusterSpacing * 0.1, w: buildingWidth * 0.95, h: buildingHeight },
      { x: center.x, y: center.y - buildingHeight * 0.8, w: buildingWidth * 1.1, h: buildingHeight },
    ];

    buildings.forEach(({ x, y, w, h }) => {
      this.#p.rect(x, y, w, h, 3);

      const roofLeftX = x - w / 2;
      const roofRightX = x + w / 2;
      const roofBaseY = y - h / 2;
      const roofPeakY = roofBaseY - roofHeight;

      this.#p.line(roofLeftX, roofBaseY, x, roofPeakY);
      this.#p.line(x, roofPeakY, roofRightX, roofBaseY);
    });
  }
}
