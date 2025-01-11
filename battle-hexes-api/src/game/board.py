class Board:
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns
        self.units = []

    def get_rows(self):
        return self.rows
  
    def get_columns(self):
        return self.columns
  
    def add_unit(self, unit, row, column):
        if row >= self.rows or column >= self.columns:
            raise Exception("Unit is out of bounds")

        unit.set_coords(row, column)
        self.units.append(unit)

    def get_units(self):
        return self.units