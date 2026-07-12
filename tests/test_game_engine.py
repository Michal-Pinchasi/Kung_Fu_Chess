import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from engin.game_engine import GameEngine

def test_game_engine_request_move_scenarios():
    board = Board(8, 8)
    w_rook = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, w_rook)
    
    engine = GameEngine(board)
    
    # 1. תרחיש סוף משחק
    engine.game_state.is_game_over = True
    res1 = engine.request_move(Position(0, 0), Position(0, 5))
    assert res1.is_accepted is False
    assert res1.reason == "game_over"
    
    engine.game_state.is_game_over = False
    
    # 2. תרחיש משבצת מקור ריקה
    res2 = engine.request_move(Position(4, 4), Position(4, 5))
    assert res2.is_accepted is False
    assert res2.reason == "empty_source"
    
    # 3. מהלך תקין והתחלת תנועה
    res3 = engine.request_move(Position(0, 0), Position(0, 5))
    assert res3.is_accepted is True

def test_game_engine_execute_command_parsing():
    board = Board(8, 8)
    w_rook = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, w_rook)
    engine = GameEngine(board)
    
    # בדיקת פענוח הפקודות הטקסטואליות
    engine.execute_command("move 0,0 to 0,5")
    assert board.get_piece(0, 0) == "." 
    
    engine.execute_command("wait 500")