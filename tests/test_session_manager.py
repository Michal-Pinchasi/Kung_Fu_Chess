from model.board import Board
from model.piece import Piece
from model.position import Position
from model.constants import PieceColor, PieceKind
from network.session_manager import SessionManager


def test_first_connection_assigned_white():
    sessions = SessionManager()
    connection = object()

    color = sessions.assign_color(connection)

    assert color == PieceColor.WHITE
    assert sessions.color_for(connection) == PieceColor.WHITE


def test_second_connection_assigned_black():
    sessions = SessionManager()
    sessions.assign_color(object())

    color = sessions.assign_color(object())

    assert color == PieceColor.BLACK


def test_third_connection_rejected_when_full():
    sessions = SessionManager()
    sessions.assign_color(object())
    sessions.assign_color(object())

    color = sessions.assign_color(object())

    assert color is None
    assert sessions.is_full() is True


def test_reassigning_same_connection_returns_same_color():
    sessions = SessionManager()
    connection = object()
    first_color = sessions.assign_color(connection)

    second_color = sessions.assign_color(connection)

    assert first_color == second_color


def test_release_frees_a_slot():
    sessions = SessionManager()
    first = object()
    sessions.assign_color(first)
    sessions.assign_color(object())
    assert sessions.is_full() is True

    sessions.release(first)

    assert sessions.is_full() is False
    assert sessions.color_for(first) is None


def test_release_unknown_connection_is_a_safe_no_op():
    sessions = SessionManager()

    sessions.release(object())  # must not raise


def test_color_for_unassigned_connection_is_none():
    sessions = SessionManager()

    assert sessions.color_for(object()) is None


def _board_with_white_and_black_pieces():
    board = Board(8, 8)
    white_rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    black_rook = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(0, 0, white_rook)
    board.add_piece(7, 0, black_rook)
    return board


def test_is_authorized_true_for_own_color_piece():
    sessions = SessionManager()
    board = _board_with_white_and_black_pieces()
    white_connection = object()
    sessions.assign_color(white_connection)

    assert sessions.is_authorized(white_connection, board, Position(0, 0)) is True


def test_is_authorized_false_for_opponent_piece():
    """A White connection must not be authorized to command a Black piece,
    even though it holds a valid color assignment."""
    sessions = SessionManager()
    board = _board_with_white_and_black_pieces()
    white_connection = object()
    sessions.assign_color(white_connection)

    assert sessions.is_authorized(white_connection, board, Position(7, 0)) is False


def test_is_authorized_false_for_unassigned_connection():
    sessions = SessionManager()
    board = _board_with_white_and_black_pieces()

    assert sessions.is_authorized(object(), board, Position(0, 0)) is False


def test_is_authorized_false_for_empty_square():
    sessions = SessionManager()
    board = _board_with_white_and_black_pieces()
    white_connection = object()
    sessions.assign_color(white_connection)

    assert sessions.is_authorized(white_connection, board, Position(3, 3)) is False
