import pytest
from Kung_Fu_Chess.model.board import Board
from Kung_Fu_Chess.model.piece import Piece
from Kung_Fu_Chess.model.constants import PieceKind, PieceColor
from Kung_Fu_Chess.io.board_printer import BoardPrinter

def test_board_printer_round_trip():
    # 1. יוצרים לוח ידנית ומציבים בו כלים
    board = Board(width=3, height=2)
    
    w_king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    b_rook = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)
    
    board.add_piece(0, 0, w_king)
    board.add_piece(1, 2, b_rook)
    
    # 2. מדפיסים את הלוח למחרוזת טקסט
    actual_text = BoardPrinter.print_board(board)
    
    # 3. הטקסט הצפוי (שורות מופרדות ברווחים וירדות שורה)
    expected_text = (
        "wK . .\n"
        ". . bR"
    )
    
    assert actual_text == expected_text