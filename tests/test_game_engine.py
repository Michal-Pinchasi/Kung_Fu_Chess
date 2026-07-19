import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from engin.game_engine import GameEngine, MoveResult
from config.config_loader import (
    JUMP_DURATION_MILLISECONDS, LONG_REST_DURATION_MILLISECONDS, SHORT_REST_DURATION_MILLISECONDS,
)


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


def test_arrival_capture_credits_the_movers_score():
    """Capturing an enemy piece on arrival awards the mover's side its point value."""
    board = Board(4, 4)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    enemy_queen = Piece(id="bQ_1", kind=PieceKind.QUEEN, color=PieceColor.BLACK)
    board.add_piece(0, 0, rook)
    board.add_piece(0, 3, enemy_queen)
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 3))
    engine.wait(3000)

    assert engine.score.white_score == 9
    assert engine.score.black_score == 0


def test_interception_credits_the_defenders_score():
    """A defender's jump killing an attacker awards the defender's side its point value.

    Uses a 1-cell queen move (1000ms) so it resolves in the same tick as the
    default 1000ms jump duration — due_moves are processed before due_jumps
    clear their status, so interception still triggers when exactly simultaneous
    (same reasoning as test_intercepted_move_does_not_begin_rest).
    """
    board = Board(4, 4)
    attacker = Piece(id="wQ_1", kind=PieceKind.QUEEN, color=PieceColor.WHITE)
    defender = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(0, 0, attacker)
    board.add_piece(1, 1, defender)
    engine = GameEngine(board)

    engine.request_jump(Position(1, 1))
    engine.request_move(Position(0, 0), Position(1, 1))  # distance 1 -> 1000ms, matches jump duration
    engine.wait(1000)

    assert engine.score.black_score == 9   # attacker (queen) was worth 9
    assert engine.score.white_score == 0


def test_snapshot_exposes_the_same_score_object():
    """snapshot().score is the same Score instance the engine tracks."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    snap = engine.snapshot()

    assert snap.score is engine.score


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


def test_request_move_blocks_same_color_race_to_same_destination():
    """Two same-color pieces cannot both be scheduled to the same destination."""
    board = Board(8, 8)
    rook1 = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    rook2 = Piece(id="wR_2", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, rook1)
    board.add_piece(7, 1, rook2)
    engine = GameEngine(board)

    dest = Position(0, 1)
    result1 = engine.request_move(Position(0, 0), dest)
    result2 = engine.request_move(Position(7, 1), dest)

    assert result1.is_accepted is True
    assert result2.is_accepted is False
    assert result2.reason == "motion_in_progress"


def test_request_move_allows_different_color_race_to_same_destination():
    """Two different-color pieces CAN both be scheduled to the same destination."""
    board = Board(8, 8)
    white_rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    black_rook = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(0, 0, white_rook)
    board.add_piece(7, 1, black_rook)
    engine = GameEngine(board)

    dest = Position(0, 1)
    result1 = engine.request_move(Position(0, 0), dest)
    result2 = engine.request_move(Position(7, 1), dest)

    assert result1.is_accepted is True
    assert result2.is_accepted is True
    assert len(engine.arbiter.pending) == 2


def test_race_to_same_square_first_arrival_then_captured_by_second():
    """The piece that lands first sits normally; the later different-color arrival captures it."""
    board = Board(8, 8)
    white_rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    black_rook = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(0, 0, white_rook)   # distance to dest = 1 -> 1000ms
    board.add_piece(0, 5, black_rook)   # distance to dest = 4 -> 4000ms
    engine = GameEngine(board)

    dest = Position(0, 1)
    result_white = engine.request_move(Position(0, 0), dest)
    result_black = engine.request_move(Position(0, 5), dest)
    assert result_white.is_accepted is True
    assert result_black.is_accepted is True

    engine.wait(1000)
    assert board.get_piece(0, 1) == white_rook
    assert white_rook.state == "long_rest"
    assert black_rook.state == "moving"

    engine.wait(3000)  # clock now at 4000ms total
    assert board.get_piece(0, 1) == black_rook
    assert white_rook.state == "captured"
    assert black_rook.state == "long_rest"


def test_resting_piece_cannot_move_again_until_rest_ends():
    """A piece in long_rest rejects a new move; once rest ends, the same move succeeds."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 1))
    engine.wait(1000)  # move lands, long_rest begins
    assert rook.state == "long_rest"

    blocked = engine.request_move(Position(0, 1), Position(0, 2))
    assert blocked.is_accepted is False
    assert blocked.reason == "motion_in_progress"

    engine.wait(LONG_REST_DURATION_MILLISECONDS)
    assert rook.state == "idle"

    allowed = engine.request_move(Position(0, 1), Position(0, 2))
    assert allowed.is_accepted is True


def test_resting_piece_cannot_jump_either():
    """A piece in long_rest also rejects a new defensive jump (full lockout)."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 1))
    engine.wait(1000)
    assert rook.state == "long_rest"

    blocked = engine.request_jump(Position(0, 1))
    assert blocked.is_accepted is False
    assert blocked.reason == "motion_in_progress"


def test_piece_in_short_rest_after_jump_cannot_act():
    """A piece in short_rest (after a jump) also rejects new moves and jumps."""
    board = Board(4, 4)
    king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, king)
    engine = GameEngine(board)

    engine.request_jump(Position(1, 1))
    engine.wait(JUMP_DURATION_MILLISECONDS)  # jump ends, short_rest begins
    assert king.state == "short_rest"

    blocked_move = engine.request_move(Position(1, 1), Position(1, 2))
    blocked_jump = engine.request_jump(Position(1, 1))
    assert blocked_move.is_accepted is False
    assert blocked_jump.is_accepted is False

    engine.wait(SHORT_REST_DURATION_MILLISECONDS)
    assert king.state == "idle"


def test_resting_piece_can_still_be_captured():
    """A piece in long_rest is still a legal capture target for an enemy move."""
    board = Board(8, 8)
    white_rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    black_rook = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(0, 0, white_rook)
    board.add_piece(3, 1, black_rook)
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 1))
    engine.wait(1000)  # white lands, enters long_rest
    assert white_rook.state == "long_rest"

    result = engine.request_move(Position(3, 1), Position(0, 1))
    assert result.is_accepted is True

    engine.wait(3000)  # black travels 3 cells
    assert board.get_piece(0, 1) == black_rook
    assert white_rook.state == "captured"


def test_idle_piece_can_flee_a_square_another_piece_is_inbound_to():
    """An idle piece can escape a square that an enemy piece is currently heading for
    (regression test: has_motion_on_path used to wrongly block this via `to == source`,
    trapping the victim even though it wasn't resting).
    """
    board = Board(8, 8)
    white_rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    black_king = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(0, 0, white_rook)   # heading to (0, 5), distance 5 -> 5000ms
    board.add_piece(0, 5, black_king)
    engine = GameEngine(board)

    result_attack = engine.request_move(Position(0, 0), Position(0, 5))
    assert result_attack.is_accepted is True

    result_flee = engine.request_move(Position(0, 5), Position(1, 5))  # distance 1 -> 1000ms
    assert result_flee.is_accepted is True

    engine.wait(1000)
    assert board.get_piece(1, 5) == black_king  # escaped in time

    engine.wait(4000)  # white's full 5000ms elapsed
    assert board.get_piece(0, 5) == white_rook   # attacker lands on the now-empty square, no capture
    assert board.get_piece(1, 5) == black_king   # king is safe where it fled to
    assert black_king.state != "captured"


def test_attacker_can_target_a_square_another_piece_is_departing_from():
    """An attacker can target the square an enemy piece is currently mid-departure
    from, and captures it if it arrives before the departure completes.
    (regression test: has_motion_on_path used to wrongly block this via
    `frm == destination`, even though RuleEngine.validate_move already handles
    live-board occupancy correctly on its own.)
    """
    board = Board(8, 8)
    white_rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    black_rook = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(0, 2, white_rook)
    board.add_piece(2, 2, black_rook)
    engine = GameEngine(board)

    result_flee = engine.request_move(Position(2, 2), Position(2, 5))    # distance 3 -> 3000ms
    assert result_flee.is_accepted is True

    result_chase = engine.request_move(Position(0, 2), Position(2, 2))   # distance 2 -> 2000ms
    assert result_chase.is_accepted is True  # previously wrongly rejected

    engine.wait(2000)  # white arrives before black finishes leaving
    assert board.get_piece(2, 2) == white_rook
    assert black_rook.state == "captured"


def test_snapshot_interpolates_position_partway_through_move():
    """Halfway through a 2-cell move, the piece snapshot sits one cell in."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 2))
    engine.wait(1000)  # half of the 2000ms duration

    snap = engine.snapshot()
    moving = next(p for p in snap.pieces if p.id == rook.id)
    assert moving.x == pytest.approx(1.0)
    assert moving.y == pytest.approx(0.0)


def test_snapshot_shows_integer_position_right_after_request():
    """Immediately after request_move (no wait yet), the piece is still exactly at source."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 2))

    snap = engine.snapshot()
    moving = next(p for p in snap.pieces if p.id == rook.id)
    assert moving.x == 0.0
    assert moving.y == 0.0


def test_snapshot_shows_destination_after_move_completes():
    """Once the move fully resolves, the snapshot shows the exact destination cell."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 2))
    engine.wait(2000)

    snap = engine.snapshot()
    landed = next(p for p in snap.pieces if p.id == rook.id)
    assert landed.x == 2.0
    assert landed.y == 0.0
    assert landed.state == "long_rest"


def test_snapshot_elapsed_state_ms_during_move():
    """snapshot() reports time-in-flight for a moving piece, for sprite-frame cycling."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 2))
    engine.wait(700)

    snap = engine.snapshot()
    moving = next(p for p in snap.pieces if p.id == rook.id)
    assert moving.elapsed_state_ms == 700


def test_snapshot_elapsed_state_ms_during_jump():
    """snapshot() reports time-in-jump for a jumping piece."""
    board = Board(4, 4)
    king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, king)
    engine = GameEngine(board)

    engine.request_jump(Position(1, 1))
    engine.wait(400)

    snap = engine.snapshot()
    jumping = next(p for p in snap.pieces if p.id == king.id)
    assert jumping.elapsed_state_ms == 400


def test_jump_at_window_pixel_requests_jump_and_sets_state():
    """A right-click pixel on a piece triggers a defensive jump."""
    board = Board(4, 4)
    king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, king)
    engine = GameEngine(board)

    from view.ui.layout.coordinate_mapper import CoordinateMapper
    px, py = CoordinateMapper.cell_center_to_pixel(1, 1)

    engine.jump_at_window_pixel(px, py)

    assert king.state == "jump"
    assert Position(1, 1) in engine.arbiter.status


def test_jump_at_window_pixel_outside_board_is_noop():
    """A right-click outside the board does nothing."""
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.jump_at_window_pixel(-100, -100)

    assert rook.state == "idle"
    assert len(engine.arbiter.pending) == 0


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
