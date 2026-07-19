import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "view", "ui")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np

from graphics.img import Img
from model.game_state import GameSnapshot
from model.score import Score
from view.ui.layout.layout import Layout
from view.ui.rendering.move_history_renderer import MoveHistoryRenderer


def _blank_frame() -> Img:
    frame = Img()
    frame.img = np.zeros((Layout.WINDOW_HEIGHT, Layout.WINDOW_WIDTH, 3), dtype="uint8")
    return frame


def _snapshot_with_score(white_score: int, black_score: int) -> GameSnapshot:
    score = Score()
    score.white_score = white_score
    score.black_score = black_score
    return GameSnapshot(
        board_width=8, board_height=8, pieces=[], selected_cell=None, game_over=False, score=score
    )


def _capture_put_text(monkeypatch, filter_prefix: str = None) -> list:
    captured = []

    def fake_put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if filter_prefix is None or txt.startswith(filter_prefix):
            captured.append((txt, x, y))

    monkeypatch.setattr(Img, "put_text", fake_put_text)
    return captured


def test_draw_score_writes_correct_text_for_both_panels(monkeypatch):
    captured = _capture_put_text(monkeypatch, filter_prefix="Score:")

    renderer = MoveHistoryRenderer()
    renderer.draw(_blank_frame(), _snapshot_with_score(white_score=12, black_score=7))

    texts = [t for t, _, _ in captured]
    assert "Score: 12" in texts
    assert "Score: 7" in texts


def test_draw_score_positions_near_the_bottom_of_each_panel(monkeypatch):
    captured = _capture_put_text(monkeypatch, filter_prefix="Score:")

    renderer = MoveHistoryRenderer()
    renderer.draw(_blank_frame(), _snapshot_with_score(white_score=3, black_score=0))

    assert len(captured) == 2
    for _, _, y in captured:
        # the score line sits in the lower half of the panel, not near the title
        assert y > Layout.WHITE_PANEL_Y + Layout.MOVE_PANEL_HEIGHT // 2


def test_no_score_drawn_when_snapshot_score_is_none(monkeypatch):
    captured = _capture_put_text(monkeypatch)

    renderer = MoveHistoryRenderer()
    snapshot = GameSnapshot(
        board_width=8, board_height=8, pieces=[], selected_cell=None, game_over=False,
        move_history=None, score=None,
    )
    renderer.draw(_blank_frame(), snapshot)

    assert not any(t.startswith("Score:") for t, _, _ in captured)
