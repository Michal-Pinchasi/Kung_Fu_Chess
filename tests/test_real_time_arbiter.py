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

    assert arbiter.has_motion_on_path(Position(0, 0), Position(3, 3), PieceColor.WHITE) is True


def test_has_motion_on_path_destination_conflict_same_color():
    """Same-color race to the same destination is blocked."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(3, 3), Position(0, 5), PieceColor.WHITE) is True


def test_has_motion_on_path_destination_conflict_different_color_allowed():
    """Different-color race to the same destination is allowed (race to capture)."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(3, 3), Position(0, 5), PieceColor.BLACK) is False


def test_has_motion_on_path_no_conflict():
    """has_motion_on_path returns False when no pending move touches the given cells."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(2, 2), Position(3, 3), PieceColor.WHITE) is False


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
    assert piece.state == "jump"


def test_advance_time_clears_jump_status_on_completion():
    """After JUMP_DURATION_MILLISECONDS, the jump is removed from status."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(3, 3, piece)

    arbiter.schedule_jump(piece, Position(3, 3))

    arbiter.advance_time(1000)

    assert Position(3, 3) not in arbiter.status
    assert len(arbiter.pending) == 0


def test_advance_time_does_not_overshoot_below_time_step():
    """A ms smaller than TIME_STEP_MS advances the clock by exactly ms, not a full step."""
    arbiter, board = _make_arbiter()

    arbiter.advance_time(33)

    assert arbiter.clock_ms == 33


def test_advance_time_accumulates_sub_step_calls_precisely():
    """Repeated small advances match the sum of their real durations."""
    arbiter, board = _make_arbiter()

    for _ in range(30):
        arbiter.advance_time(33)

    assert arbiter.clock_ms == 990


def test_get_move_progress_none_for_idle_piece():
    """An idle piece with no pending move has no progress."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    assert arbiter.get_move_progress(piece) is None


def test_get_move_progress_zero_right_after_scheduling():
    """Progress is 0.0 immediately after scheduling a move."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 2))

    frm, to, progress = arbiter.get_move_progress(piece)
    assert frm == Position(0, 0)
    assert to == Position(0, 2)
    assert progress == 0.0


def test_get_state_elapsed_ms_zero_for_idle_piece():
    """A piece with no pending activity has zero elapsed state time."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    assert arbiter.get_state_elapsed_ms(piece) == 0


def test_get_state_elapsed_ms_during_move():
    """Elapsed ms tracks the clock partway through a move."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 2))
    arbiter.clock_ms = 700

    assert arbiter.get_state_elapsed_ms(piece) == 700


def test_get_state_elapsed_ms_during_jump():
    """Elapsed ms tracks the clock partway through a defensive jump."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(3, 3, piece)

    arbiter.schedule_jump(piece, Position(3, 3))
    arbiter.clock_ms = 400

    assert arbiter.get_state_elapsed_ms(piece) == 400


def test_get_move_progress_full_before_resolution():
    """Progress reaches 1.0 once the full duration has elapsed, before advance_time resolves it."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 2))
    arbiter.clock_ms = 2000  # full 2-cell duration elapsed, but advance_time not called

    _, _, progress = arbiter.get_move_progress(piece)
    assert progress == 1.0
