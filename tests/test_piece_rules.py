import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from rules.piece_rules import PieceRules


def test_rook_moves_clear_and_blocked():
    """Rook slides in 4 directions and stops at a blocker (enemy is included)."""
    board = Board(width=5, height=5)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(2, 2, rook)
    blocker = Piece(id="bP_1", kind=PieceKind.PAWN, color=PieceColor.BLACK)
    board.add_piece(2, 4, blocker)

    destinations = PieceRules.legal_destinations(board, rook, Position(2, 2))

    expected = {
        Position(0, 2), Position(1, 2), Position(3, 2), Position(4, 2),
        Position(2, 0), Position(2, 1), Position(2, 3), Position(2, 4),
    }
    assert destinations == expected


def test_rook_blocked_by_friendly():
    """Rook cannot move to or past a friendly piece."""
    board = Board(4, 4)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    friendly = Piece(id="wP_1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(0, 0, rook)
    board.add_piece(0, 2, friendly)

    destinations = PieceRules.legal_destinations(board, rook, Position(0, 0))

    assert Position(0, 2) not in destinations
    assert Position(0, 3) not in destinations
    assert Position(0, 1) in destinations


def test_bishop_moves():
    """Bishop moves diagonally and not straight."""
    board = Board(width=4, height=4)
    bishop = Piece(id="wB_1", kind=PieceKind.BISHOP, color=PieceColor.WHITE)
    board.add_piece(0, 0, bishop)

    destinations = PieceRules.legal_destinations(board, bishop, Position(0, 0))

    assert destinations == {Position(1, 1), Position(2, 2), Position(3, 3)}
    assert Position(0, 1) not in destinations


def test_queen_combines_rook_and_bishop():
    """Queen moves in all 8 directions."""
    board = Board(3, 3)
    queen = Piece(id="wQ_1", kind=PieceKind.QUEEN, color=PieceColor.WHITE)
    board.add_piece(1, 1, queen)

    destinations = PieceRules.legal_destinations(board, queen, Position(1, 1))

    assert len(destinations) == 8


def test_knight_moves_near_board_edges():
    """Knight L-shapes that fall outside the board are filtered out."""
    board = Board(width=3, height=3)
    knight = Piece(id="wN_1", kind=PieceKind.KNIGHT, color=PieceColor.WHITE)
    board.add_piece(0, 0, knight)

    destinations = PieceRules.legal_destinations(board, knight, Position(0, 0))

    assert destinations == {Position(1, 2), Position(2, 1)}


def test_king_moves():
    """King moves exactly one step in any of the 8 directions."""
    board = Board(width=3, height=3)
    king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, king)

    destinations = PieceRules.legal_destinations(board, king, Position(1, 1))

    assert len(destinations) == 8


def test_white_pawn_forward_only_on_non_start_row():
    """White pawn on a non-starting row can move one step forward and capture diagonally."""
    # White's starting row is fixed at row 1, so row 2 is NOT the starting row
    board = Board(width=3, height=5)
    pawn = Piece(id="wP_1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(2, 1, pawn)
    enemy = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(3, 2, enemy)

    destinations = PieceRules.legal_destinations(board, pawn, Position(2, 1))

    assert destinations == {Position(3, 1), Position(3, 2)}


def test_pawn_double_move_from_start_row():
    """White pawn on the starting row (row 1) can move two steps forward."""
    board = Board(width=3, height=4)
    pawn = Piece(id="wP_1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(1, 1, pawn)

    destinations = PieceRules.legal_destinations(board, pawn, Position(1, 1))

    assert Position(2, 1) in destinations  # one step
    assert Position(3, 1) in destinations  # two steps


def test_pawn_double_move_blocked_by_intermediate():
    """Double move is blocked when the intermediate cell is occupied."""
    board = Board(width=3, height=4)
    pawn = Piece(id="wP_1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(2, 1, pawn)
    blocker = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(1, 1, blocker)

    destinations = PieceRules.legal_destinations(board, pawn, Position(2, 1))

    assert Position(1, 1) not in destinations
    assert Position(0, 1) not in destinations


def test_pawn_cannot_capture_forward():
    """Pawn cannot move forward into an occupied cell."""
    board = Board(3, 3)
    pawn = Piece(id="wP_1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    blocker = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    board.add_piece(2, 1, pawn)
    board.add_piece(1, 1, blocker)

    destinations = PieceRules.legal_destinations(board, pawn, Position(2, 1))

    assert Position(1, 1) not in destinations


def test_unknown_piece_kind_returns_empty_set():
    """An unknown piece kind returns an empty destination set."""
    board = Board(width=3, height=3)
    fake_piece = Piece(id="wX_1", kind=None, color=PieceColor.WHITE)

    destinations = PieceRules.legal_destinations(board, fake_piece, Position(0, 0))

    assert destinations == set()
