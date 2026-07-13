import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from engin.game_engine import GameEngine, MoveResult


def _board_with_rook():
    board = Board(8, 8)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, rook)
    return board, rook


def test_request_move_rejected_when_game_over():
    board, _ = _board_with_rook()
    engine = GameEngine(board)
    engine.game_state.is_game_over = True

    result = engine.request_move(Position(0, 0), Position(0, 5))

    assert isinstance(result, MoveResult)
    assert result.is_accepted is False
    assert result.reason == "game_over"


def test_request_move_rejected_when_empty_source():
    board, _ = _board_with_rook()
    engine = GameEngine(board)

    result = engine.request_move(Position(4, 4), Position(4, 5))

    assert result.is_accepted is False
    assert result.reason == "empty_source"


def test_request_move_rejected_when_illegal_shape():
    board, _ = _board_with_rook()
    engine = GameEngine(board)

    result = engine.request_move(Position(0, 0), Position(3, 3))  # rook cannot move diagonally

    assert result.is_accepted is False
    assert result.reason == "illegal_piece_move"


def test_request_move_accepted_and_piece_stays_at_source():
    """After a legal request_move, the piece remains at its source until wait() completes."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    result = engine.request_move(Position(0, 0), Position(0, 5))

    assert result.is_accepted is True
    assert board.get_piece(0, 0) == rook  # still at source
    assert len(engine.arbiter.pending) == 1


def test_request_move_rejected_when_motion_in_progress():
    """A second move request is rejected while the first is still active."""
    board, _ = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 5))
    result = engine.request_move(Position(0, 0), Position(0, 3))

    assert result.is_accepted is False
    assert result.reason == "motion_in_progress"


def test_wait_completes_move_and_updates_board():
    """After wait() for the full duration, the piece appears at the destination."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 5))
    engine.wait(5000)  # 5 cells × 1000 ms

    assert board.get_piece(0, 0) == "."
    assert board.get_piece(0, 5) == rook


def test_wait_partial_time_does_not_move_piece():
    """Waiting for less than the travel duration leaves the board unchanged."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 5))
    engine.wait(2000)  # only 2 of 5 seconds

    assert board.get_piece(0, 0) == rook
    assert board.get_piece(0, 5) == "."


def test_capture_enemy_on_arrival():
    """Arriving at an enemy-occupied cell removes the enemy and places the mover."""
    board = Board(4, 4)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    enemy = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(0, 0, rook)
    board.add_piece(0, 3, enemy)
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 3))
    engine.wait(3000)

    assert board.get_piece(0, 0) == "."
    assert board.get_piece(0, 3) == rook
    assert enemy.state == "captured"


def test_king_capture_sets_game_over():
    """Capturing the enemy king sets game_over and records the winner."""
    board = Board(4, 4)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    w_king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    b_king = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(0, 0, rook)
    board.add_piece(3, 3, w_king)  # white king must exist for winner detection
    board.add_piece(0, 3, b_king)
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 3))
    engine.wait(3000)

    assert engine.game_state.is_game_over is True
    assert engine.game_state.winner == "WHITE"


def test_move_result_is_frozen_dataclass():
    """MoveResult is immutable — attribute assignment must raise."""
    result = MoveResult(is_accepted=True, reason="ok")
    with pytest.raises(Exception):
        result.is_accepted = False


def test_is_cell_empty_query():
    board = Board(4, 4)
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, piece)
    engine = GameEngine(board)

    assert engine.is_cell_empty(Position(0, 0)) is True
    assert engine.is_cell_empty(Position(1, 1)) is False


def test_is_friendly_piece_query():
    board = Board(4, 4)
    white = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    black = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(0, 0, white)
    board.add_piece(0, 1, black)
    board.add_piece(0, 2, Piece(id="wB_1", kind=PieceKind.BISHOP, color=PieceColor.WHITE))
    engine = GameEngine(board)

    assert engine.is_friendly_piece(Position(0, 2), Position(0, 0)) is True   # both white
    assert engine.is_friendly_piece(Position(0, 1), Position(0, 0)) is False  # different colors
    assert engine.is_friendly_piece(Position(3, 3), Position(0, 0)) is False  # empty cell


def test_snapshot_returns_correct_data():
    """snapshot() returns a GameSnapshot with accurate piece and board info."""
    board = Board(4, 4)
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)
    engine = GameEngine(board)

    snap = engine.snapshot()

    assert snap.board_width == 4
    assert snap.board_height == 4
    assert len(snap.pieces) == 1
    assert snap.pieces[0].color == "w"
    assert snap.pieces[0].kind == "R"
    assert snap.game_over is False
