from graphics.img import Img
from view.ui.layout.layout import Layout


class BoardRenderer:
    """Draws the chess board image onto a frame.

    Loads the board image once at construction time and blits it onto
    whatever frame is passed to draw().
    """

    def __init__(self, board_path: str):
        self._board_img = Img().read(
            board_path,
            size=(Layout.BOARD_SIZE, Layout.BOARD_SIZE)
        )

    def draw(self, frame: Img) -> None:
        """Draw the board onto frame at the position defined in Layout."""
        self._board_img.draw_on(frame, Layout.BOARD_X, Layout.BOARD_Y)
