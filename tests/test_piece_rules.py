import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from rules.piece_rules import PieceRules

def test_rook_moves_clear_and_blocked():
    """1. בדיקת צריח: וידוא תנועה ב-4 כיוונים ועצירה כשנחסם על ידי כלי"""
    board = Board(width=5, height=5)
    # תוקן סדר הפרמטרים: id, kind, color
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(2, 2, rook)

    blocker = Piece(id="bP_1", kind=PieceKind.PAWN, color=PieceColor.BLACK)
    board.add_piece(2, 4, blocker)

    destinations = PieceRules.legal_destinations(board, rook, Position(2, 2))

    expected_moves = {
        Position(0, 2), Position(1, 2), Position(3, 2), Position(4, 2),
        Position(2, 0), Position(2, 1), Position(2, 3), Position(2, 4)
    }
    assert destinations == expected_moves

def test_bishop_moves():
    """2. בדיקת רץ: וידוא תנועה חופשית באלכסונים"""
    board = Board(width=4, height=4)
    bishop = Piece(id="wB_1", kind=PieceKind.BISHOP, color=PieceColor.WHITE)
    board.add_piece(0, 0, bishop)

    destinations = PieceRules.legal_destinations(board, bishop, Position(0, 0))
    expected_moves = {Position(1, 1), Position(2, 2), Position(3, 3)}
    assert destinations == expected_moves

def test_knight_moves_near_board_edges():
    """3. בדיקת פרש: וידוא סינון קפיצות L שחורגות מגבולות הלוח"""
    board = Board(width=3, height=3)
    knight = Piece(id="wN_1", kind=PieceKind.KNIGHT, color=PieceColor.WHITE)
    board.add_piece(0, 0, knight)

    destinations = PieceRules.legal_destinations(board, knight, Position(0, 0))
    expected_moves = {Position(1, 2), Position(2, 1)}
    assert destinations == expected_moves

def test_king_moves():
    """4. בדיקת מלך: וידוא תנועה של צעד אחד לכל 8 הכיוונים"""
    board = Board(width=3, height=3)
    king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, king)

    destinations = PieceRules.legal_destinations(board, king, Position(1, 1))
    assert len(destinations) == 8

def test_white_pawn_forward_and_diagonal_capture():
    """5. בדיקת רגלי לבן: צעד קדימה לריק ואכילה באלכסון כשיש אויב"""
    board = Board(width=3, height=3)
    pawn = Piece(id="wP_1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(2, 1, pawn)

    enemy = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(1, 2, enemy)

    destinations = PieceRules.legal_destinations(board, pawn, Position(2, 1))
    expected_moves = {Position(1, 1), Position(1, 2)}
    assert destinations == expected_moves

def test_unknown_piece_kind_returns_empty_set():
    """6. בדיקת הגנה: סוג כלי לא מוכר מחזיר קבוצה ריקה"""
    board = Board(width=3, height=3)
    fake_piece = Piece(id="wX_1", kind=None, color=PieceColor.WHITE)
    
    destinations = PieceRules.legal_destinations(board, fake_piece, Position(0, 0))
    assert destinations == set()