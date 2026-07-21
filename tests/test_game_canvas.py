"""
Visual test for GameCanvas.

Loads the background image, draws the board on top of it,
and displays the result in a window.

Run manually with:
    python -m pytest tests/test_game_canvas.py -v -s
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "view", "ui")))

from view.ui.window.game_canvas import GameCanvas
from view.ui.layout.layout import Layout
from graphics.img import Img

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "view", "ui", "assets")
BACKGROUND_PATH = os.path.join(ASSETS_DIR, "back_graound.jpg")
BOARD_PATH = os.path.join(ASSETS_DIR, "board.jpg")


def test_background_loads_successfully():
    """GameCanvas loads the background image without raising."""
    canvas = GameCanvas(BACKGROUND_PATH)

    assert canvas.fresh_frame() is not None
    assert canvas.fresh_frame().img is not None


def test_background_has_valid_dimensions():
    """The loaded background image has positive width and height."""
    canvas = GameCanvas(BACKGROUND_PATH)
    h, w = canvas.fresh_frame().img.shape[:2]

    assert w > 0
    assert h > 0


def test_board_draws_on_background():
    """The board image can be placed on top of the background without errors."""
    canvas = GameCanvas(BACKGROUND_PATH)
    board_img = Img().read(BOARD_PATH, size=(Layout.BOARD_SIZE, Layout.BOARD_SIZE))
    frame = canvas.fresh_frame()
    board_img.draw_on(frame, Layout.BOARD_X, Layout.BOARD_Y)
    assert frame.img is not None


@pytest.mark.skip(reason="manual OpenCV visual check; not an automated test")
def test_visual_display(request):
    """
    Visual test — opens a window showing the board on the background.
    Press any key to close the window.
    """
    canvas = GameCanvas(BACKGROUND_PATH)
    board_img = Img().read(BOARD_PATH, size=(Layout.BOARD_SIZE, Layout.BOARD_SIZE))
    frame = canvas.fresh_frame()
    board_img.draw_on(frame, Layout.BOARD_X, Layout.BOARD_Y)
    canvas.show(frame)
