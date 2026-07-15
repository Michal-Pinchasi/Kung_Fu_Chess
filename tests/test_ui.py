"""
Unit tests for the UI layer.

Tests cover:
- CoordinateMapper (cell ↔ pixel conversions)
- ui_config_loader (all keys present and correct types)
- GameCanvas (loads background, fresh_frame returns copy)
- BoardRenderer (draws without error)
- OverlayRenderer (selection highlight, game-over overlay)
- GameScene (render pipeline produces a frame)

Visual/interactive components (MouseHandler, full app loop) are
not tested here — they require a display and real input.
"""

import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "view", "ui")))

from view.ui.layout.layout import Layout
from view.ui.layout.coordinate_mapper import CoordinateMapper
from view.ui.config.ui_config_loader import (
    WINDOW_TITLE, FPS, SELECTION_COLOR, PIECE_SIZE_FRACTION,
    GAME_OVER_TEXT, GAME_OVER_FONT_SIZE,
)

_UI_DIR   = os.path.join(os.path.dirname(__file__), "..", "view", "ui")
_ASSETS   = os.path.join(_UI_DIR, "assets")
_BG_PATH  = os.path.join(_ASSETS, "back_graound.jpg")
_BRD_PATH = os.path.join(_ASSETS, "board.jpg")


# ── CoordinateMapper ────────────────────────────────────────────────────────

class TestCoordinateMapper:

    def test_cell_to_pixel_origin(self):
        """Cell (0,0) maps to (BOARD_X + BOARD_BORDER, BOARD_Y + BOARD_BORDER)."""
        x, y = CoordinateMapper.cell_to_pixel(0, 0)
        assert x == Layout.BOARD_X + Layout.BOARD_BORDER
        assert y == Layout.BOARD_Y + Layout.BOARD_BORDER

    def test_cell_to_pixel_offset(self):
        """Cell (1,2) maps correctly accounting for border."""
        x, y = CoordinateMapper.cell_to_pixel(1, 2)
        assert x == Layout.BOARD_X + Layout.BOARD_BORDER + 2 * Layout.SQUARE_SIZE
        assert y == Layout.BOARD_Y + Layout.BOARD_BORDER + 1 * Layout.SQUARE_SIZE

    def test_cell_center_is_offset_by_half(self):
        cx, cy = CoordinateMapper.cell_center_to_pixel(0, 0)
        assert cx == Layout.BOARD_X + Layout.BOARD_BORDER + Layout.SQUARE_SIZE // 2
        assert cy == Layout.BOARD_Y + Layout.BOARD_BORDER + Layout.SQUARE_SIZE // 2

    def test_pixel_to_cell_round_trip(self):
        """cell_to_pixel followed by pixel_to_cell returns the original cell."""
        for row in range(4):
            for col in range(4):
                px, py = CoordinateMapper.cell_to_pixel(row, col)
                result = CoordinateMapper.pixel_to_cell(px, py)
                assert result == (row, col)

    def test_pixel_to_cell_outside_board_returns_none(self):
        """Pixels above or left of the board return None."""
        assert CoordinateMapper.pixel_to_cell(0, 0) is None

    def test_pixel_to_cell_exact_boundary(self):
        """The top-left pixel of the playing area maps to cell (0,0)."""
        result = CoordinateMapper.pixel_to_cell(
            Layout.BOARD_X + Layout.BOARD_BORDER,
            Layout.BOARD_Y + Layout.BOARD_BORDER
        )
        assert result == (0, 0)


# ── ui_config_loader ────────────────────────────────────────────────────────

class TestUiConfigLoader:

    def test_window_title_is_string(self):
        assert isinstance(WINDOW_TITLE, str)
        assert len(WINDOW_TITLE) > 0

    def test_fps_is_positive_int(self):
        assert isinstance(FPS, int)
        assert FPS > 0

    def test_selection_color_has_four_channels(self):
        assert len(SELECTION_COLOR) == 4

    def test_piece_size_fraction_between_0_and_1(self):
        assert 0.0 < PIECE_SIZE_FRACTION <= 1.0

    def test_game_over_text_is_string(self):
        assert isinstance(GAME_OVER_TEXT, str)

    def test_game_over_font_size_positive(self):
        assert GAME_OVER_FONT_SIZE > 0


# ── GameCanvas ──────────────────────────────────────────────────────────────

class TestGameCanvas:

    def test_loads_background(self):
        from view.ui.window.game_canvas import GameCanvas
        canvas = GameCanvas(_BG_PATH)
        frame = canvas.fresh_frame()
        assert frame.img is not None

    def test_fresh_frame_is_correct_size(self):
        from view.ui.window.game_canvas import GameCanvas
        canvas = GameCanvas(_BG_PATH)
        frame = canvas.fresh_frame()
        h, w = frame.img.shape[:2]
        assert w == Layout.WINDOW_WIDTH
        assert h == Layout.WINDOW_HEIGHT

    def test_fresh_frame_returns_independent_copy(self):
        """Mutating one frame must not affect the next fresh_frame."""
        from view.ui.window.game_canvas import GameCanvas
        canvas = GameCanvas(_BG_PATH)
        frame1 = canvas.fresh_frame()
        frame1.img[:] = 0            # zero out the entire frame
        frame2 = canvas.fresh_frame()
        assert frame2.img.sum() > 0  # background is still intact


# ── BoardRenderer ───────────────────────────────────────────────────────────

class TestBoardRenderer:

    def test_draw_does_not_raise(self):
        from view.ui.window.game_canvas import GameCanvas
        from view.ui.rendering.board_renderer import BoardRenderer
        canvas = GameCanvas(_BG_PATH)
        renderer = BoardRenderer(_BRD_PATH)
        frame = canvas.fresh_frame()
        renderer.draw(frame)   # must not raise


# ── OverlayRenderer ─────────────────────────────────────────────────────────

class TestOverlayRenderer:

    def _make_frame(self):
        from view.ui.window.game_canvas import GameCanvas
        return GameCanvas(_BG_PATH).fresh_frame()

    def _make_snapshot(self, selected=None, game_over=False):
        from model.game_state import GameSnapshot
        snap = GameSnapshot(
            board_width=8,
            board_height=8,
            pieces=[],
            selected_cell=selected,
            game_over=game_over,
        )
        if game_over:
            snap.winner = "WHITE"
        return snap

    def test_no_selection_does_not_raise(self):
        from view.ui.rendering.overlay_renderer import OverlayRenderer
        renderer = OverlayRenderer()
        frame = self._make_frame()
        renderer.draw(frame, self._make_snapshot())

    def test_selection_modifies_frame(self):
        from view.ui.rendering.overlay_renderer import OverlayRenderer
        from model.position import Position
        renderer = OverlayRenderer()
        frame = self._make_frame()
        before = frame.img.copy()
        renderer.draw(frame, self._make_snapshot(selected=Position(0, 0)))
        assert not np.array_equal(frame.img, before)

    def test_game_over_modifies_frame(self):
        from view.ui.rendering.overlay_renderer import OverlayRenderer
        renderer = OverlayRenderer()
        frame = self._make_frame()
        before = frame.img.copy()
        renderer.draw(frame, self._make_snapshot(game_over=True))
        assert not np.array_equal(frame.img, before)


# ── GameScene ───────────────────────────────────────────────────────────────

class TestGameScene:

    def test_render_returns_frame_with_correct_size(self):
        from view.ui.window.game_canvas import GameCanvas
        from view.ui.rendering.board_renderer import BoardRenderer
        from view.ui.rendering.piece_renderer import PieceRenderer
        from view.ui.rendering.overlay_renderer import OverlayRenderer
        from view.ui.scene.game_scene import GameScene
        from storage.board_parser import BoardParser
        from engin.game_engine import GameEngine

        board  = BoardParser.parse(". . .\n. . .\n. . .")
        engine = GameEngine(board)

        scene = GameScene(
            canvas           = GameCanvas(_BG_PATH),
            board_renderer   = BoardRenderer(_BRD_PATH),
            piece_renderer   = PieceRenderer(os.path.join(_ASSETS, "pieces")),
            overlay_renderer = OverlayRenderer(),
            engine           = engine,
        )

        frame = scene.render()
        h, w = frame.img.shape[:2]
        assert w == Layout.WINDOW_WIDTH
        assert h == Layout.WINDOW_HEIGHT
