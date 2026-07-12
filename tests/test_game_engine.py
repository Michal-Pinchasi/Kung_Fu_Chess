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
    
    engine.game_state.is_game_over = True
    res1 = engine.request_move(Position(0, 0), Position(0, 5))
    assert res1.is_accepted is False
    assert res1.reason == "game_over"
    
    engine.game_state.is_game_over = False
    
    res2 = engine.request_move(Position(4, 4), Position(4, 5))
    assert res2.is_accepted is False
    assert res2.reason == "empty_source"
    
    res3 = engine.request_move(Position(0, 0), Position(0, 5))
    assert res3.is_accepted is True
    assert w_rook.state == "moving"
    
    res4 = engine.request_move(Position(0, 5), Position(0, 6))
    assert res4.is_accepted is False
    assert res4.reason == "motion_in_progress"

def test_game_engine_wait_and_game_over_flow():
    board = Board(8, 8)
    w_rook = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    b_king = Piece(id="b_k", kind=PieceKind.KING, color=PieceColor.BLACK)
    
    board.add_piece(0, 0, w_rook)
    board.add_piece(0, 5, b_king)
    
    engine = GameEngine(board)
    engine.request_move(Position(0, 0), Position(0, 5))
    
    engine.wait(1000)
    
    assert engine.game_state.is_game_over is True
    assert engine.game_state.winner == "WHITE"