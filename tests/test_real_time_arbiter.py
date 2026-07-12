import pytest
from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from realtime.real_time_arbiter import RealTimeArbiter

def test_arbiter_has_motion_on_path_all_cases():
    board = Board(8, 8)
    arbiter = RealTimeArbiter(board)
    piece = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    
    src = Position(0, 0)
    dst = Position(0, 5)
    arbiter.start_motion(piece, src, dst, duration_ticks=10)
    
    assert arbiter.has_motion_on_path(Position(0, 0), Position(4, 4)) is True
    assert arbiter.has_motion_on_path(Position(3, 3), Position(0, 5)) is True
    assert arbiter.has_motion_on_path(Position(3, 3), Position(0, 0)) is True
    assert arbiter.has_motion_on_path(Position(0, 5), Position(4, 4)) is True
    
    assert arbiter.has_motion_on_path(Position(2, 2), Position(3, 3)) is False

def test_advance_time_granular_ticks():
    board = Board(8, 8)
    arbiter = RealTimeArbiter(board)
    piece = Piece(id="w_p", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(1, 1, piece)
    
    arbiter.start_motion(piece, Position(1, 1), Position(2, 1), duration_ticks=2)
    
    arbiter.advance_time(50)
    assert len(arbiter.active_motions) == 1
    
    arbiter.advance_time(100)
    assert len(arbiter.active_motions) == 1
    
    arbiter.advance_time(100)
    assert len(arbiter.active_motions) == 0
    assert board.get_piece(2, 1) == piece