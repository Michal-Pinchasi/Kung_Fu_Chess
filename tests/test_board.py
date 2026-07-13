import pytest
from model.board import Board
from model.piece import Piece
from model.position import Position
from model.constants import PieceKind, PieceColor

def test_board_bounds_and_validity():
    board = Board(width=4, height=3)
    assert board.is_valid_position(0, 0) is True
    assert board.is_valid_position(2, 3) is True
    assert board.is_valid_position(-1, 0) is False
    assert board.is_valid_position(3, 0) is False
    assert board.is_valid_position(0, 4) is False

def test_board_add_and_get_piece():
    board = Board(width=3, height=3)
    piece = Piece(id="wR1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    
    assert board.add_piece(1, 1, piece) is True
    assert board.get_piece(1, 1) == piece
    
    # הוספה על משבצת תפוסה או מחוץ ללוח
    piece2 = Piece(id="bK1", kind=PieceKind.KING, color=PieceColor.BLACK)
    assert board.add_piece(1, 1, piece2) is False
    assert board.add_piece(5, 5, piece2) is False
    assert board.get_piece(5, 5) == "."

def test_board_remove_and_move_piece():
    board = Board(width=4, height=4)
    piece = Piece(id="wP1", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)
    
    board.move_piece(Position(0, 0), Position(2, 2))
    assert board.get_piece(0, 0) == "."
    assert board.get_piece(2, 2) == piece
    
    # מקרים לא חוקיים של תנועה
    board.move_piece(Position(0, 0), Position(3, 3))  # מקור ריק
    board.move_piece(Position(2, 2), Position(10, 10)) # יעד מחוץ ללוח
    assert board.get_piece(2, 2) == piece

def test_board_set_piece():
    board = Board(width=3, height=3)
    piece = Piece(id="wQ", kind=PieceKind.QUEEN, color=PieceColor.WHITE)
    board.set_piece(0, 0, piece)
    assert board.get_piece(0, 0) == piece