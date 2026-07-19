import pytest
from model.position import Position
from model.board import Board
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from input.controller import Controller
from engin.game_engine import GameEngine, MoveResult
from view.ui.layout.coordinate_mapper import CoordinateMapper


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


def test_handle_pixel_click_selects_and_clears_out_of_bounds():
    """A real GUI pixel click on a piece selects it; a click out of bounds clears selection."""
    board = Board(8, 8)
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)
    engine = GameEngine(board)
    controller = engine.controller

    px, py = CoordinateMapper.cell_center_to_pixel(0, 0)
    controller.handle_pixel_click(px, py)
    assert controller.selected_cell == Position(0, 0)

    controller.handle_pixel_click(-100, -100)
    assert controller.selected_cell is None


def test_handle_pixel_click_sends_move_on_second_click():
    """Two real GUI pixel clicks (select, then destination) issue a move request."""
    board = Board(8, 8)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, rook)
    engine = GameEngine(board)
    controller = engine.controller

    px1, py1 = CoordinateMapper.cell_center_to_pixel(0, 0)
    px2, py2 = CoordinateMapper.cell_center_to_pixel(0, 5)
    controller.handle_pixel_click(px1, py1)
    controller.handle_pixel_click(px2, py2)

    assert controller.selected_cell is None
    assert len(engine.arbiter.pending) == 1  # move was scheduled


def test_handle_pixel_jump_requests_jump_and_sets_state():
    """A real GUI right-click pixel on a piece triggers a defensive jump."""
    board = Board(4, 4)
    king = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(1, 1, king)
    engine = GameEngine(board)
    controller = engine.controller

    px, py = CoordinateMapper.cell_center_to_pixel(1, 1)
    controller.handle_pixel_jump(px, py)

    assert king.state == "jump"
    assert Position(1, 1) in engine.arbiter.status


def test_handle_pixel_jump_outside_board_is_noop():
    """A right-click pixel outside the board does nothing."""
    board = Board(8, 8)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, rook)
    engine = GameEngine(board)
    controller = engine.controller

    controller.handle_pixel_jump(-100, -100)

    assert rook.state == "idle"
    assert len(engine.arbiter.pending) == 0


def test_run_script_prints_board_directly(capsys):
    """A 'print board' command prints via BoardPrinter, not through execute_command."""
    board = Board(2, 2)
    piece = Piece(id="wK_1", kind=PieceKind.KING, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece)
    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    controller.run_script(["print board"])

    captured = capsys.readouterr()
    assert "wK" in captured.out


def test_run_script_delegates_other_commands_to_execute_command():
    """Non-print commands (click, jump, wait) still run via execute_command."""
    board = Board(8, 8)
    piece1 = Piece(id="w_r", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, piece1)
    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    controller.run_script(["click 50 50", "click 550 50"])

    assert fake_engine.last_move_request == (Position(0, 0), Position(0, 5))


def test_run_script_skips_blank_lines():
    board = Board(4, 4)
    fake_engine = FakeGameEngine(board)
    controller = Controller(fake_engine)

    controller.run_script(["", "   "])  # should not raise
