import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from realtime.real_time_arbiter import RealTimeArbiter
from realtime.motion import PendingMove
from config.config_loader import (
    JUMP_DURATION_MILLISECONDS, LONG_REST_DURATION_MILLISECONDS, SHORT_REST_DURATION_MILLISECONDS,
)


def _make_arbiter():
    board = Board(8, 8)
    return RealTimeArbiter(board), board


def test_has_motion_on_path_destination_conflict_same_color():
    """Same-color race to the same destination is blocked."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(0, 5), PieceColor.WHITE) is True


def test_has_motion_on_path_destination_conflict_different_color_allowed():
    """Different-color race to the same destination is allowed (race to capture)."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(0, 5), PieceColor.BLACK) is False


def test_has_motion_on_path_no_conflict():
    """has_motion_on_path returns False when no pending move targets that destination."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 5))

    assert arbiter.has_motion_on_path(Position(3, 3), PieceColor.WHITE) is False


def test_has_motion_on_path_does_not_block_fleeing_the_attacked_square():
    """A piece whose own square is another piece's inbound destination is NOT
    blocked by has_motion_on_path — fleeing an incoming capture must stay possible.
    This is the bug fix: has_motion_on_path only inspects `destination`, so a piece's
    own current square (which happens to equal an attacker's `to`) never conflicts
    with the piece's escape destination unless that escape target coincides with
    someone else's same-color destination.
    """
    arbiter, board = _make_arbiter()
    attacker = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, attacker)

    arbiter.schedule_move(attacker, Position(0, 0), Position(0, 5))  # heading for the victim's square

    # The victim (black, currently sitting at (0,5)) tries to flee to (1,5).
    assert arbiter.has_motion_on_path(Position(1, 5), PieceColor.BLACK) is False


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
    """A one-cell move completes after MILLISECONDS_PER_CELL ms, then begins a long_rest."""
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

    # After full duration: move completes, and a long_rest PendingRest takes its place
    arbiter.advance_time(500)
    assert len(arbiter.pending) == 1
    assert piece.state == "long_rest"


def test_advance_time_two_cells_takes_two_seconds():
    """A two-cell move takes 2000 ms total, then begins a long_rest."""
    board = Board(4, 4)
    arbiter = RealTimeArbiter(board)
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 2))

    arbiter.advance_time(1000)
    assert len(arbiter.pending) == 1  # not yet arrived

    arbiter.advance_time(1000)
    assert len(arbiter.pending) == 1  # arrived, now resting
    assert piece.state == "long_rest"


def test_schedule_jump_registers_status():
    """schedule_jump records a Jumping status for the cell."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(3, 3, piece)

    arbiter.schedule_jump(piece, Position(3, 3))

    assert Position(3, 3) in arbiter.status
    assert piece.state == "jump"


def test_advance_time_clears_jump_status_on_completion():
    """After JUMP_DURATION_MILLISECONDS, the jump is removed from status and short_rest begins."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(3, 3, piece)

    arbiter.schedule_jump(piece, Position(3, 3))

    arbiter.advance_time(1000)

    assert Position(3, 3) not in arbiter.status
    assert len(arbiter.pending) == 1
    assert piece.state == "short_rest"


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


def test_long_rest_ends_and_returns_piece_to_idle():
    """After LONG_REST_DURATION_MILLISECONDS, a resting piece returns to idle."""
    board = Board(4, 4)
    arbiter = RealTimeArbiter(board)
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 1))  # 1000ms travel
    arbiter.advance_time(1000)
    assert piece.state == "long_rest"

    arbiter.advance_time(LONG_REST_DURATION_MILLISECONDS)
    assert piece.state == "idle"
    assert len(arbiter.pending) == 0


def test_short_rest_ends_and_returns_piece_to_idle():
    """After SHORT_REST_DURATION_MILLISECONDS, a resting piece returns to idle."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(3, 3, piece)

    arbiter.schedule_jump(piece, Position(3, 3))
    arbiter.advance_time(JUMP_DURATION_MILLISECONDS)
    assert piece.state == "short_rest"

    arbiter.advance_time(SHORT_REST_DURATION_MILLISECONDS)
    assert piece.state == "idle"
    assert len(arbiter.pending) == 0


def test_intercepted_move_does_not_begin_rest():
    """A piece stopped mid-flight by an enemy jump is captured, not rested.

    Uses a 1-cell move (the shortest possible, 1000ms) against the default
    1000ms jump duration so both resolve in the same tick — due_moves are
    processed before due_jumps clear their status, so interception still
    triggers correctly even though they're exactly simultaneous.
    """
    arbiter, board = _make_arbiter()
    attacker = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    defender = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(0, 2, attacker)
    board.add_piece(0, 3, defender)

    arbiter.schedule_jump(defender, Position(0, 3))
    arbiter.schedule_move(attacker, Position(0, 2), Position(0, 3))

    intercepted, finished_moves, _, finished_rests, _ = arbiter.advance_time(1000)

    assert len(intercepted) == 1
    assert finished_moves == []
    assert finished_rests == []
    assert attacker.state == "moving"  # GameEngine.wait() is what flips this to "captured"


def test_get_move_progress_full_before_resolution():
    """Progress reaches 1.0 once the full duration has elapsed, before advance_time resolves it."""
    arbiter, board = _make_arbiter()
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)

    arbiter.schedule_move(piece, Position(0, 0), Position(0, 2))
    arbiter.clock_ms = 2000  # full 2-cell duration elapsed, but advance_time not called

    _, _, progress = arbiter.get_move_progress(piece)
    assert progress == 1.0
