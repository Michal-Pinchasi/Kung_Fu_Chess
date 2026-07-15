import copy
from graphics.img import Img
from view.ui.layout.layout import Layout


class GameCanvas:
    """The main canvas of the game.

    Loads the background once and exposes a clean frame each render cycle.
    Every renderer draws on the canvas returned by fresh_frame().
    """

    def __init__(self, background_path: str):
        self._background = Img().read(
            background_path,
            size=(Layout.WINDOW_WIDTH, Layout.WINDOW_HEIGHT)
        )

    def fresh_frame(self) -> Img:
        """Return a deep copy of the background ready for a new frame."""
        frame = Img()
        frame.img = self._background.img.copy()
        return frame

    def show(self, frame: Img) -> None:
        """Display a completed frame in the window."""
        frame.show()
