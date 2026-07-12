import pytest
from model.position import Position
from model.board import Board
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from input.controller import Controller
from engin.game_engine import ExecuteResult

class FakeGameEngine:
    def __init__(self, board):
        self.board = board
        self.last_move_request = None

    def request_move(self, source: Position, destination: Position):
        self.last_move_request = (source, destination)
        return ExecuteResult(True, "ok")

def test_controller_selection_policy():
    board = Board(8, 8)
    piece1 = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    piece2 = Piece(id="w_p", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece1)
    board.add_piece(0, 1, piece2)
    
    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    # 1. לחיצה על ריק כשאין בחירה
    controller.click(50, 500) 
    assert controller.selected_cell is None

    # 2. לחיצה על כלי -> מסמנת אותו
    controller.click(50, 50) 
    assert controller.selected_cell == Position(0, 0)

    # 3. לחיצה על כלי אחר מאותו צבע -> מחליפה בחירה
    controller.click(150, 50) 
    assert controller.selected_cell == Position(0, 1)

    # 4. לחיצה מחוץ ללוח כשיש כלי נבחר -> מבטלת בחירה
    controller.click(850, 50) 
    assert controller.selected_cell is None
    assert fake_engine.last_move_request is None

    # 5. לחיצה שנייה ביעד ריק -> שולחת מהלך ומאפסת
    controller.click(50, 50) 
    controller.click(550, 50) 
    assert controller.selected_cell is None
    assert fake_engine.last_move_request == (Position(0, 0), Position(0, 5))