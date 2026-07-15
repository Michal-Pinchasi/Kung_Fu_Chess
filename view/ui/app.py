"""
Application entry point for Kung Fu Chess UI.
"""

import os
import sys
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from storage.board_parser import BoardParser
from engin.game_engine import GameEngine
from view.ui.window.game_canvas import GameCanvas
from view.ui.rendering.board_renderer import BoardRenderer
from view.ui.rendering.piece_renderer import PieceRenderer
from view.ui.rendering.overlay_renderer import OverlayRenderer
from view.ui.scene.game_scene import GameScene
from view.ui.input.mouse_handler import MouseHandler
from view.ui.config.ui_config_loader import FPS, WINDOW_TITLE

_UI_DIR         = os.path.dirname(__file__)
ASSETS_DIR      = os.path.join(_UI_DIR, "assets")
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "back_graound.jpg")
BOARD_PATH      = os.path.join(ASSETS_DIR, "board.jpg")
PIECES_DIR      = os.path.join(ASSETS_DIR, "pieces2")

_DEFAULT_BOARD = """\
wR wN wB wQ wK wB wN wR
wP wP wP wP wP wP wP wP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
bP bP bP bP bP bP bP bP
bR bN bB bQ bK bB bN bR"""


def app(board_text: str = _DEFAULT_BOARD) -> None:
    """Start the Kung Fu Chess game window."""
    board  = BoardParser.parse(board_text)
    engine = GameEngine(board)

    canvas           = GameCanvas(BACKGROUND_PATH)
    board_renderer   = BoardRenderer(BOARD_PATH)
    piece_renderer   = PieceRenderer(PIECES_DIR)
    overlay_renderer = OverlayRenderer()
    scene            = GameScene(canvas, board_renderer, piece_renderer,
                                 overlay_renderer, engine)
    mouse_handler = MouseHandler(engine)

    window_name = WINDOW_TITLE
    ms_per_frame = 1000 // FPS

    # Render one frame first to know the image dimensions,
    # then create the window at exactly that size — no scaling, 1:1 pixels.
    first_frame = scene.render()
    img_h, img_w = first_frame.img.shape[:2]

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, img_w, img_h)
    cv2.imshow(window_name, first_frame.img)

    # Register callback AFTER imshow so the window exists
    mouse_handler.register(window_name)

    cv2.waitKey(1)   # flush the event queue once

    while True:
        frame = scene.render()
        cv2.imshow(window_name, frame.img)

        key = cv2.waitKey(ms_per_frame) & 0xFF
        if key == ord("q") or key == 27:
            break

        engine.wait(ms_per_frame)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    app()
