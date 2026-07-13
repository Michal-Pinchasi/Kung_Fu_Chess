from model.position import Position
from config.constants import CELL_SIZE


class BoardMapper:
    """Translates pixel coordinates into logical board cells.

    Knows only about CELL_SIZE and board dimensions. Has no knowledge
    of game rules, piece state, or rendering.
    """

    @staticmethod
    def pixel_to_cell(x: int, y: int, width: int, height: int) -> Position | None:
        """Convert pixel coordinates to a board Position.

        Returns None when the mapped cell is outside the board bounds.
        """
        col = x // CELL_SIZE
        row = y // CELL_SIZE
        if 0 <= row < height and 0 <= col < width:
            return Position(row, col)
        return None
