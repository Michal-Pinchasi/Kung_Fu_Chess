from model.position import Position


class Board:
    """Owns the logical arrangement of pieces on a rectangular grid.

    Responsibilities:
    - Store width and height.
    - Add, remove, and query pieces by cell.
    - Validate whether a cell is within bounds.
    - Move a piece after validation has already happened elsewhere.

    Board does not contain chess movement rules and does not call RuleEngine.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [["." for _ in range(width)] for _ in range(height)]

    def is_valid_position(self, row: int, col: int) -> bool:
        """Return True when (row, col) is within board bounds."""
        return 0 <= row < self.height and 0 <= col < self.width

    def get_piece(self, row: int, col: int):
        """Return the piece at (row, col), or '.' for empty or out-of-bounds."""
        if not self.is_valid_position(row, col):
            return "."
        return self.grid[row][col]

    def add_piece(self, row: int, col: int, piece) -> bool:
        """Place a piece on an empty cell. Return False if out of bounds or already occupied."""
        if not self.is_valid_position(row, col):
            return False
        if self.grid[row][col] != ".":
            return False
        self.grid[row][col] = piece
        return True

    def remove_piece(self, row: int, col: int) -> None:
        """Clear the cell at (row, col), replacing its content with '.'."""
        if self.is_valid_position(row, col):
            self.grid[row][col] = "."

    def set_piece(self, row: int, col: int, piece) -> None:
        """Directly place a piece at (row, col), overwriting any existing occupant.

        Used by RealTimeArbiter on arrival. Assumes the caller has already
        handled capture logic.
        """
        if self.is_valid_position(row, col):
            self.grid[row][col] = piece

    def move_piece(self, source: Position, destination: Position) -> None:
        """Move a piece from source to destination without any rule validation.

        Does nothing when source is empty or either position is out of bounds.
        """
        if not self.is_valid_position(source.row, source.col):
            return
        if not self.is_valid_position(destination.row, destination.col):
            return
        piece = self.get_piece(source.row, source.col)
        if piece == ".":
            return
        self.remove_piece(source.row, source.col)
        self.grid[destination.row][destination.col] = piece
