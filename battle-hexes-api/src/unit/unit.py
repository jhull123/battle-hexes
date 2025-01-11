class Unit:
    def __init__(self):
        self.row = None
        self.column = None

    def set_coords(self, row, column):
        self.row = row
        self.column = column
    
    def get_coords(self):
        return (self.row, self.column)