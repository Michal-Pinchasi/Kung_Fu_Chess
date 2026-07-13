import pytest
from model.position import Position
from model.board import Board
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from input.controller import Controller
from engin.game_engine import MoveResult


class FakeGameEngine:
    """Minimal fake engine for controller unit tests.

    Exposes the same query and command interface as GameEngine without
    running real chess logic.
    """

    def __init__(self, board: Board):
        self.board = board
        self.last_move_request = None
        self.game_state = type("gs", (), {"is_game_over": False})()

    def is_cell_empty(self, position: Position) -> bool:
        piece = self.board.get_piece(position.row, position.col)
        return piece == "." or piece is None

    def is_friendly_piece(self, position: Position, reference: Position) -> bool:
        piece = self.board.get_piece(position.row, position.col)
        ref_piece = self.board.get_piece(reference.row, reference.col)
        if piece == "." or piece is None:
            return False
        if ref_piece == "." or ref_piece is None:
            return False
        return piece.color == ref_piece.color

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        self.last_move_request = (source, destination)
        return MoveResult(is_accepted=True, reason="ok")

    def request_jump(self, position: Position) -> MoveResult:
        return MoveResult(is_accepted=True, reason="ok")

    def wait(self, ms: int) -> None:
        pass


def test_controller_selection_policy():
    board = Board(8, 8)
    piece1 = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    piece2 = Piece(id="w_p", kind=PieceKind.PAWN, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece1)
    board.add_piece(0, 1, piece2)

    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    # 1. First click on empty cell — no selection
    controller.click(50, 500)
    assert controller.selected_cell is None

    # 2. First click on a piece — selects it
    controller.click(50, 50)
    assert controller.selected_cell == Position(0, 0)

    # 3. Second click on friendly piece — switches selection
    controller.click(150, 50)
    assert controller.selected_cell == Position(0, 1)

    # 4. Out-of-bounds click while piece selected — clears selection, no move sent
    controller.click(850, 50)
    assert controller.selected_cell is None
    assert fake_engine.last_move_request is None

    # 5. Second click on empty destination — sends move and clears selection
    controller.click(50, 50)
    controller.click(550, 50)
    assert controller.selected_cell is None
    assert fake_engine.last_move_request == (Position(0, 0), Position(0, 5))


def test_controller_oob_ignored_when_no_selection():
    """Out-of-bounds click with no selection should be silently ignored."""
    board = Board(4, 4)
    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    controller.click(9999, 9999)
    assert controller.selected_cell is None
    assert fake_engine.last_move_request is None


def test_controller_same_cell_click_does_not_send_move():
    """Clicking the same cell twice should not call request_move."""
    board = Board(4, 4)
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, piece)
    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    controller.click(150, 150)
    controller.click(150, 150)
    assert fake_engine.last_move_request is None
