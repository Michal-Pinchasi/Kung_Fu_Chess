import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "view", "ui")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graphics.img import Img
from model.game_state import GameSnapshot, PieceSnapshot
from view.ui.layout.layout import Layout
from view.ui.rendering.piece_renderer import PieceRenderer

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "view", "ui", "assets")
_PIECES_DIR = os.path.join(_ASSETS, "pieces2")


def _snapshot_with_piece(x: float, y: float) -> GameSnapshot:
    piece = PieceSnapshot(id="wR_1", kind="R", color="w", x=x, y=y, state="idle")
    return GameSnapshot(board_width=8, board_height=8, pieces=[piece], selected_cell=None, game_over=False)


def _snapshot_with_state(state: str, elapsed_state_ms: int) -> GameSnapshot:
    piece = PieceSnapshot(
        id="wR_1", kind="R", color="w", x=0.0, y=0.0,
        state=state, elapsed_state_ms=elapsed_state_ms,
    )
    return GameSnapshot(board_width=8, board_height=8, pieces=[piece], selected_cell=None, game_over=False)


def _captured_draw_x(monkeypatch, x: float, y: float) -> int:
    """Render a single piece at (x, y) and return the pixel x it was drawn at."""
    captured = {}

    def fake_draw_on(self, other_img, dx, dy):
        captured["x"] = dx
        captured["y"] = dy

    monkeypatch.setattr(Img, "draw_on", fake_draw_on)

    renderer = PieceRenderer(_PIECES_DIR)
    frame = Img()
    renderer.draw(frame, _snapshot_with_piece(x, y))

    assert captured, "sprite.draw_on was never called — check pieces2/RW sprites exist"
    return captured


def test_fractional_x_shifts_pixel_by_expected_amount(monkeypatch):
    """A piece drawn half a cell further right lands half a SQUARE_SIZE further in pixels."""
    at_zero = _captured_draw_x(monkeypatch, x=0.0, y=0.0)
    at_half = _captured_draw_x(monkeypatch, x=0.5, y=0.0)

    delta = at_half["x"] - at_zero["x"]
    assert delta == round(0.5 * Layout.SQUARE_SIZE)


def test_fractional_y_shifts_pixel_by_expected_amount(monkeypatch):
    """A piece drawn a quarter cell further down lands a quarter SQUARE_SIZE further in pixels."""
    at_zero = _captured_draw_x(monkeypatch, x=0.0, y=0.0)
    at_quarter = _captured_draw_x(monkeypatch, x=0.0, y=0.25)

    delta = at_quarter["y"] - at_zero["y"]
    assert delta == round(0.25 * Layout.SQUARE_SIZE)


def test_integer_position_matches_cell_to_pixel_center(monkeypatch):
    """At an integer cell position, the sprite is centred in the same cell as the discrete mapper."""
    from view.ui.layout.coordinate_mapper import CoordinateMapper

    captured = _captured_draw_x(monkeypatch, x=2.0, y=1.0)
    cell_px, cell_py = CoordinateMapper.cell_to_pixel(1, 2)

    # sprite is centred within the square, so its top-left is within one square of the cell origin
    assert cell_px <= captured["x"] < cell_px + Layout.SQUARE_SIZE
    assert cell_py <= captured["y"] < cell_py + Layout.SQUARE_SIZE


def test_moving_state_cycles_through_five_frames(monkeypatch):
    """A moving piece's sprite frame advances through 1-5 as elapsed_state_ms grows."""
    monkeypatch.setattr(Img, "draw_on", lambda self, other_img, dx, dy: None)

    renderer = PieceRenderer(_PIECES_DIR)
    frame = Img()
    for elapsed in (0, 100, 200, 300, 400):
        renderer.draw(frame, _snapshot_with_state("moving", elapsed))

    used_frames = {key[-1] for key in renderer._cache if key.startswith("Rwmoving")}
    assert used_frames == {"1", "2", "3", "4", "5"}


def test_moving_state_frame_wraps_after_full_cycle(monkeypatch):
    """After 5 frames worth of elapsed time, the cycle wraps back to frame 1."""
    monkeypatch.setattr(Img, "draw_on", lambda self, other_img, dx, dy: None)

    renderer = PieceRenderer(_PIECES_DIR)
    frame = Img()
    renderer.draw(frame, _snapshot_with_state("moving", 0))
    renderer.draw(frame, _snapshot_with_state("moving", 500))  # one full cycle later (5 * 100ms)

    assert "Rwmoving1" in renderer._cache
    assert "Rwmoving5" not in renderer._cache  # 500ms wraps to frame 1, not frame 5


def test_jump_state_also_cycles_frames(monkeypatch):
    """A jumping piece's sprite frame also advances with elapsed_state_ms."""
    monkeypatch.setattr(Img, "draw_on", lambda self, other_img, dx, dy: None)

    renderer = PieceRenderer(_PIECES_DIR)
    frame = Img()
    renderer.draw(frame, _snapshot_with_state("jump", 300))

    assert "Rwjump4" in renderer._cache


def test_idle_state_always_uses_frame_one(monkeypatch):
    """Idle pieces never animate, regardless of elapsed_state_ms."""
    monkeypatch.setattr(Img, "draw_on", lambda self, other_img, dx, dy: None)

    renderer = PieceRenderer(_PIECES_DIR)
    frame = Img()
    renderer.draw(frame, _snapshot_with_state("idle", 999999))

    assert "Rwidle1" in renderer._cache
    assert not any(key.startswith("Rwidle") and key != "Rwidle1" for key in renderer._cache)
