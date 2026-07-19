import pytest
from storage.board_parser import (
    BoardParser, EmptyBoardError, RowWidthMismatchError, UnknownPieceTokenError,
)
from model.constants import PieceKind, PieceColor

def test_parse_valid_board():
    board_text = (
        "wK . .\n"
        ". . bR"
    )
    board = BoardParser.parse(board_text)

    assert board.height == 2
    assert board.width == 3

    w_king = board.get_piece(0, 0)
    assert w_king != "."
    assert w_king.kind == PieceKind.KING
    assert w_king.color == PieceColor.WHITE

    assert board.get_piece(0, 1) == "."

    b_rook = board.get_piece(1, 2)
    assert b_rook != "."
    assert b_rook.kind == PieceKind.ROOK
    assert b_rook.color == PieceColor.BLACK

def test_parse_invalid_row_lengths():
    bad_text = (
        "wK . .\n"
        ". bR"
    )
    with pytest.raises(ValueError):
        BoardParser.parse(bad_text)

def test_parse_invalid_token():
    bad_text = "wK . wX"
    with pytest.raises(ValueError):
        BoardParser.parse(bad_text)

def test_parse_empty_board_raises_specific_type():
    with pytest.raises(EmptyBoardError):
        BoardParser.parse("")

def test_parse_row_width_mismatch_raises_specific_type():
    bad_text = (
        "wK . .\n"
        ". bR"
    )
    with pytest.raises(RowWidthMismatchError):
        BoardParser.parse(bad_text)

def test_parse_bad_token_length_raises_specific_type():
    with pytest.raises(UnknownPieceTokenError):
        BoardParser.parse("wK . wXX")

def test_parse_unknown_color_or_kind_raises_specific_type():
    with pytest.raises(UnknownPieceTokenError):
        BoardParser.parse("wK . wX")