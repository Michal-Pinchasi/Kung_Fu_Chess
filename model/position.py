class Position:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def __eq__(self, other):
        """מאפשר להשוות בין שני מיקומים בעזרת =="""
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self):
        """מאפשר להכניס את המיקום לתוך set או מילון"""
        return hash((self.row, self.col))

    def __repr__(self):
        return f"Position({self.row}, {self.col})"