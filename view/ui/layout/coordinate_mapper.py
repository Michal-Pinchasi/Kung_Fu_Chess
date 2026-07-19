from typing import Optional, Tuple
from view.ui.layout.layout import Layout


class CoordinateMapper:
    """Stateless converter between board cells and pixel positions."""

    @staticmethod
    def cell_to_pixel(row: int, col: int) -> Tuple[int, int]:
        """Return the top-left pixel corner of the cell at (row, col)."""
        x = Layout.BOARD_X + Layout.BOARD_BORDER + col * Layout.SQUARE_SIZE
        y = Layout.BOARD_Y + Layout.BOARD_BORDER + row * Layout.SQUARE_SIZE
        return x, y

    @staticmethod
    def cell_to_pixel_f(row: float, col: float) -> Tuple[float, float]:
        """Float-precision version for interpolated animation positions."""
        x = Layout.BOARD_X + Layout.BOARD_BORDER + col * Layout.SQUARE_SIZE
        y = Layout.BOARD_Y + Layout.BOARD_BORDER + row * Layout.SQUARE_SIZE
        return x, y

    @staticmethod
    def cell_center_to_pixel(row: int, col: int) -> Tuple[int, int]:
        """Return the pixel centre of the cell at (row, col)."""
        x, y = CoordinateMapper.cell_to_pixel(row, col)
        return x + Layout.SQUARE_CENTER_OFFSET, y + Layout.SQUARE_CENTER_OFFSET

    @staticmethod
    def pixel_to_cell(px: int, py: int) -> Optional[Tuple[int, int]]:
        """Return (row, col) for the given pixel, or None if outside the board."""
        inner_x = px - Layout.BOARD_X - Layout.BOARD_BORDER
        inner_y = py - Layout.BOARD_Y - Layout.BOARD_BORDER
        
        if inner_x < 0 or inner_y < 0:
            return None
            
        col = inner_x // Layout.SQUARE_SIZE
        row = inner_y // Layout.SQUARE_SIZE
        
        if col >= Layout.BOARD_COLS or row >= Layout.BOARD_ROWS:
            return None
            
        return row, col