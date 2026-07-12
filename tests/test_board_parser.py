import pytest
from Kung_Fu_Chess.io.board_parser import BoardParser
from Kung_Fu_Chess.model.constants import PieceKind, PieceColor

def test_parse_valid_board():
    board_text = (
        "wK . .\n"
        ". . bR"
    )
    # ה-Parser מסיק את הגודל מהטקסט: 2 שורות, 3 עמודות
    board = BoardParser.parse(board_text)
    
    assert board.height == 2
    assert board.width == 3
    
    # בדיקת הכלי הלבן ב-(0,0)
    w_king = board.get_piece(0, 0)
    assert w_king != "."
    assert w_king.kind == PieceKind.KING
    assert w_king.color == PieceColor.WHITE
    
    # בדיקת המשבצת הריקה
    assert board.get_piece(0, 1) == "."
    
    # בדיקת הצריח השחור ב-(1,2)
    b_rook = board.get_piece(1, 2)
    assert b_rook != "."
    assert b_rook.kind == PieceKind.ROOK
    assert b_rook.color == PieceColor.BLACK

def test_parse_invalid_row_lengths():
    # שורה ראשונה באורך 3, שורה שנייה באורך 2 - לא חוקי!
    bad_text = (
        "wK . .\n"
        ". bR"
    )
    with pytest.raises(ValueError):
        BoardParser.parse(bad_text)

def test_parse_invalid_token():
    # תו מומצא שאינו כלי חוקי
    bad_text = "wK . wX"
    with pytest.raises(ValueError):
        BoardParser.parse(bad_text)