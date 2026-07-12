import pytest
from model.board import Board
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from storage.board_printer import BoardPrinter

def test_board_printer_round_trip():
    board = Board(width=3, height=2)

    w_king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    b_rook = Piece(id="bR_1", kind=PieceKind.ROOK, color=PieceColor.BLACK)

    board.add_piece(0, 0, w_king)
    board.add_piece(1, 2, b_rook)

    actual_text = BoardPrinter.print_board(board)

    expected_text = (
        "wK . .\n"
        ". . bR"
    )

    assert actual_text == expected_text