import pytest
from model.board import Board
from model.game_state import GameState, GameSnapshot, PieceSnapshot
from model.position import Position
from engin.game_engine import MoveResult


def test_game_state_initialization():
    board = Board(width=8, height=8)
    state = GameState(board)

    assert state.board is board
    assert state.is_game_over is False
    assert state.winner is None


def test_game_state_can_be_set_to_over():
    board = Board(4, 4)
    state = GameState(board)

    state.is_game_over = True
    state.winner = "WHITE"

    assert state.is_game_over is True
    assert state.winner == "WHITE"


def test_game_snapshot_stores_all_fields():
    piece_snap = PieceSnapshot(id="wR_1", kind="R", color="w", x=1.0, y=2.0, state="idle")
    snapshot = GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[piece_snap],
        selected_cell=Position(0, 0),
        game_over=True,
    )

    assert snapshot.board_width == 8
    assert snapshot.board_height == 8
    assert len(snapshot.pieces) == 1
    assert snapshot.pieces[0].id == "wR_1"
    assert snapshot.selected_cell == Position(0, 0)
    assert snapshot.game_over is True


def test_piece_snapshot_fields():
    snap = PieceSnapshot(id="bK_1", kind="K", color="b", x=3.0, y=5.0, state="moving")

    assert snap.id == "bK_1"
    assert snap.kind == "K"
    assert snap.color == "b"
    assert snap.x == 3.0
    assert snap.y == 5.0
    assert snap.state == "moving"


def test_move_result_accepted():
    result = MoveResult(is_accepted=True, reason="ok")

    assert result.is_accepted is True
    assert result.reason == "ok"


def test_move_result_rejected():
    result = MoveResult(is_accepted=False, reason="motion_in_progress")

    assert result.is_accepted is False
    assert result.reason == "motion_in_progress"


def test_move_result_is_frozen():
    result = MoveResult(is_accepted=True, reason="ok")

    with pytest.raises(Exception):
        result.is_accepted = False
