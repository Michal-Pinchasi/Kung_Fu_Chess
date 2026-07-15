"""
GameScene coordinates one complete render frame.

Pipeline (per frame):
1. Ask the engine for a fresh snapshot.
2. Get a clean background frame from GameCanvas.
3. BoardRenderer draws the board.
4. PieceRenderer draws all pieces.
5. OverlayRenderer draws selection and game-over.
6. Return the finished frame to the caller.
"""

from graphics.img import Img
from view.ui.window.game_canvas import GameCanvas
from view.ui.rendering.board_renderer import BoardRenderer
from view.ui.rendering.piece_renderer import PieceRenderer
from view.ui.rendering.overlay_renderer import OverlayRenderer


class GameScene:
    """Coordinates all renderers to produce one complete frame.

    GameScene never reads the board directly and never calls game rules.
    It only consumes the engine snapshot and delegates drawing.
    """

    def __init__(
        self,
        canvas: GameCanvas,
        board_renderer: BoardRenderer,
        piece_renderer: PieceRenderer,
        overlay_renderer: OverlayRenderer,
        engine,
    ):
        self._canvas = canvas
        self._board_renderer = board_renderer
        self._piece_renderer = piece_renderer
        self._overlay_renderer = overlay_renderer
        self._engine = engine

    def render(self) -> Img:
        """Build and return one complete frame."""
        snapshot = self._engine.snapshot()
        frame = self._canvas.fresh_frame()

        self._board_renderer.draw(frame)
        self._piece_renderer.draw(frame, snapshot)
        self._overlay_renderer.draw(frame, snapshot)

        return frame
