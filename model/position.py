class Position:
    """Represents a logical board cell by row and column.

    This is a pure value object. It has no knowledge of board size,
    pixel coordinates, movement rules, or game state.
    """

    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def __eq__(self, other) -> bool:
        """Return True when both row and column match."""
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        """Allow Position to be used as a dict key or set member."""
        return hash((self.row, self.col))

    def __repr__(self) -> str:
        return f"Position({self.row}, {self.col})"
