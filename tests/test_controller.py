import pytest
from model.position import Position
from model.board import Board
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from Kung_Fu_Chess.input.controller import Controller
# מחלקת דמה (Fake) כדי לבדוק את הנתונים שה-Controller שולח ל-GameEngine
class FakeGameEngine:
    def __init__(self, board):
        self.board = board
        self.last_move_request = None

    def request_move(self, source: Position, destination: Position):
        self.last_move_request = (source, destination)
        # מחזירים אובייקט דמה עם reason="ok" כדי לדמות תגובה מהמנוע
        class FakeResult:
            is_accepted = True
            reason = "ok"
        return FakeResult()

def test_controller_selection_policy():
    board = Board(8, 8)
    # נציב כלי ב-(0,0) משבצת (0,5) תישאר ריקה
    piece = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)
    
    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    # 1. לחיצה ראשונה על משבצת ריקה (0,5) -> לא צריכה לבחור כלום
    controller.click(50, 500) # x=50, y=500 -> row=5, col=0
    assert controller.selected_cell is None

    # 2. לחיצה ראשונה על כלי (0,0) -> מסמנת את הכלי כנבחר
    controller.click(50, 50) # x=50, y=50 -> row=0, col=0
    assert controller.selected_cell == Position(0, 0)

    # 3. לחיצה מחוץ ללוח כשיש כלי נבחר -> מבטלת את הבחירה
    controller.click(850, 50) # מחוץ ללוח
    assert controller.selected_cell is None
    assert fake_engine.last_move_request is None

    # 4. לחיצה שנייה בתוך הלוח -> שולחת מהלך למנוע ומנקה את הבחירה
    controller.click(50, 50) # בחירה מחדש של הכלי ב-(0,0)
    assert controller.selected_cell == Position(0, 0)
    
    controller.click(550, 50) # לחיצה שניה ביעד (row=0, col=5)
    # מוודאים שהבחירה התנקה מיד
    assert controller.selected_cell is None
    # מוודאים שהבקשה נשלחה למנוע עם הפרמטרים הנכונים
    assert fake_engine.last_move_request == (Position(0, 0), Position(0, 5))