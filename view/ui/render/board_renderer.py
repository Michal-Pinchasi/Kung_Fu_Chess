from graphics.img import Img
from view.ui.layout.layout import Layout


class BoardRenderer:
    """Draws the board image onto the canvas at the position defined in Layout."""

    def __init__(self, canvas, board_path: str, x: int, y: int):
        self._canvas = canvas
        self._board_img = Img().read(
            board_path,
            size=(Layout.BOARD_SIZE, Layout.BOARD_SIZE)
        )
        self._x = x
        self._y = y

    def draw(self) -> None:
        """Draw the board onto the canvas at (x, y)."""
        self._board_img.draw_on(self._canvas.canvas, self._x, self._y)
