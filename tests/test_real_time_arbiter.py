import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from realtime.real_time_arbiter import RealTimeArbiter
from realtime.motion import PendingMove


def _make_arbiter():
    board = Board(8, 8)
    return RealTimeArbiter(board), board


def test_has_motion_on_path_source_conflict():
    """has_motion_on_path returns True when a pending move starts at the given source."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(0, 0), Position(3, 3)) is True


def test_has_motion_on_path_destination_conflict():
    """has_motion_on_path returns True when a pending move ends at the given destination."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(3, 3), Position(0, 5)) is True


def test_has_motion_on_path_no_conflict():
    """has_motion_on_path returns False when no pending move touches the given cells."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(2, 2), Position(3, 3)) is False


def test_schedule_move_sets_piece_state():
    """schedule_move marks the piece as moving."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wB_1", kind=PieceKind.BISHOP, color=PieceColor.WHITE)
    board.add_piece(1, 1, piece)

    arbiter.schedule_move(piece, Position(1, 1), Position(3, 3))

    assert piece.state == "moving"
    assert len(arbiter.pending) == 1
    assert isinstance(arbiter.pending[0], PendingMove)


def test_advance_time_piece_arrives_after_full_duration():
    """A one-cell move completes after MILLISECONDS_PER_CELL ms."""
    board = Board(4, 4)
    arbiter = RealTimeArbiter(board)
    piece = Piece(id="wP_1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(1, 1, piece)

    arbiter.schedule_move(piece, Position(1, 1), Position(2, 1))

    # Before arrival: piece not yet at destination
    arbiter.advance_time(500)
    assert board.get_piece(1, 1) == piece
    assert board.get_piece(2, 1) == "."
    assert len(arbiter.pending) == 1

    # After full duration: move completes
    arbiter.advance_time(500)
    assert len(arbiter.pending) == 0


def test_advance_time_two_cells_takes_two_seconds():
    """A two-cell move takes 2000 ms total."""
    board = Board(4, 4)
    arbiter = RealTimeArbiter(board)
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 2))

    arbiter.advance_time(1000)
    assert len(arbiter.pending) == 1  # not yet arrived

    arbiter.advance_time(1000)
    assert len(arbiter.pending) == 0  # arrived


def test_schedule_jump_registers_status():
    """schedule_jump records a Jumping status for the cell."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(3, 3, piece)

    arbiter.schedule_jump(piece, Position(3, 3))

    assert Position(3, 3) in arbiter.status
    assert piece.state == "moving"


def test_advance_time_clears_jump_status_on_completion():
    """After JUMP_DURATION_MILLISECONDS, the jump is removed from status."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(3, 3, piece)

    arbiter.schedule_jump(piece, Position(3, 3))

    arbiter.advance_time(1000)

    assert Position(3, 3) not in arbiter.status
    assert len(arbiter.pending) == 0
