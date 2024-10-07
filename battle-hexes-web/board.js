class Board {
    #hexMap;
    #selectedHex;
    #moveHoverHex;
  
    constructor(rows, columns) {
      this.hexMap = new Map();
  
      for (let row = 0; row < rows; row++) {
        for (let column = 0; column < columns; column++) {
          this.hexMap.set(`${row},${column}`, new Hex(row, column));
        }
      }
    }
  
    getHex(row, column) {
      return this.hexMap.get(`${row},${column}`);
    }
  
    getHexStrCoord(strCoord) {
      return this.hexMap.get(strCoord);
    }
  
    getAllHexes() {
      return this.hexMap.values();
    }
  
    select(hexToSelect) {
        this.selectedHex = hexToSelect;
    }
  
    deselect() {
        let oldSelection = this.selectedHex;
        this.selectedHex = undefined;
        return oldSelection;
    }
  
    isSelected(aHex) {
      return aHex !== undefined && this.selectedHex === aHex;
    }
  
    hasSelection() {
      return this.selectedHex !== undefined;
    }
  
    setMoveHoverHex(hoverHex) {
      this.moveHoverHex = hoverHex;
    }
  
    dehover() {
      let oldHover = this.moveHoverHex;
      this.moveHoverHex = undefined;
      return oldHover;
    }
  
    isHovered(aHex) {
      return aHex !== undefined && this.moveHoverHex === aHex;
    }
  }