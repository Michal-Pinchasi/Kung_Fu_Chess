import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from rules.rule_engine import RuleEngine

def test_validate_move_all_branches():
    board = Board(8, 8)
    white_rook = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    friendly_pawn = Piece(id="w_p", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    
    board.add_piece(4, 4, white_rook)
    board.add_piece(4, 6, friendly_pawn)
    
    # 1. בדיקת משבצת מקור ריקה
    res1 = RuleEngine.validate_move(board, Position(0, 0), Position(0, 1))
    assert res1.is_valid is False
    assert res1.reason == "empty_source"
    
    # 2. בדיקת יעד מחוץ ללוח
    res2 = RuleEngine.validate_move(board, Position(4, 4), Position(8, 4))
    assert res2.is_valid is False
    assert res2.reason == "outside_board"
    
    # 3. בדיקת יעד עם כלי ידידותי
    res3 = RuleEngine.validate_move(board, Position(4, 4), Position(4, 6))
    assert res3.is_valid is False
    assert res3.reason == "friendly_destination"
    
    # 4. בדיקת מהלך גיאומטרית לא חוקי
    res4 = RuleEngine.validate_move(board, Position(4, 4), Position(5, 5))
    assert res4.is_valid is False
    assert res4.reason == "illegal_piece_move"
    
    # 5. מהלך תקין לחלוטין
    res5 = RuleEngine.validate_move(board, Position(4, 4), Position(4, 5))
    assert res5.is_valid is True
    assert res5.reason == "ok"

def test_get_game_winner_all_states():
    board = Board(8, 8)
    w_king = Piece(id="w_k", kind=PieceKind.KING, color=PieceColor.WHITE)
    b_king = Piece(id="b_k", kind=PieceKind.KING, color=PieceColor.BLACK)
    
    board.add_piece(0, 4, w_king)
    board.add_piece(7, 4, b_king)
    assert RuleEngine.get_game_winner(board) is None
    
    board.remove_piece(0, 4)
    assert RuleEngine.get_game_winner(board) == "BLACK"
    
    board.remove_piece(7, 4)
    board.add_piece(0, 4, w_king)
    assert RuleEngine.get_game_winner(board) == "WHITE"