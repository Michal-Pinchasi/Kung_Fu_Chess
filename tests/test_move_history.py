from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from model.move_history import Move, MoveHistory
from engin.game_engine import GameEngine


def test_add_move_routes_by_color():
    history = MoveHistory()
    history.add_move("w", Position(6, 4), Position(4, 4), "P", False)
    history.add_move("b", Position(1, 4), Position(3, 4), "P", False)

    assert history.get_white_moves() == [Move(Position(6, 4), Position(4, 4), "P", False)]
    assert history.get_black_moves() == [Move(Position(1, 4), Position(3, 4), "P", False)]


def test_get_moves_returns_a_copy():
    history = MoveHistory()
    history.add_move("w", Position(6, 4), Position(4, 4), "P", False)

    history.get_white_moves().append("tampered")

    assert len(history.get_white_moves()) == 1


def test_clear_empties_both_lists():
    history = MoveHistory()
    history.add_move("w", Position(6, 4), Position(4, 4), "P", False)
    history.add_move("b", Position(1, 4), Position(3, 4), "P", False)

    history.clear()

    assert history.get_white_moves() == []
    assert history.get_black_moves() == []


def _board_with_rook():
    board = Board(8, 8)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    board.add_piece(0, 0, rook)
    return board, rook


def test_wait_records_completed_move_in_engine_history():
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 5))
    engine.wait(5000)

    white_moves = engine.move_history.get_white_moves()
    assert len(white_moves) == 1
    assert white_moves[0].source == Position(0, 0)
    assert white_moves[0].destination == Position(0, 5)
    assert white_moves[0].piece_kind == "R"
    assert white_moves[0].is_capture is False
    assert engine.move_history.get_black_moves() == []


def test_wait_records_capture_flag():
    board = Board(4, 4)
    rook = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    enemy = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    board.add_piece(0, 0, rook)
    board.add_piece(0, 3, enemy)
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 3))
    engine.wait(3000)

    white_moves = engine.move_history.get_white_moves()
    assert len(white_moves) == 1
    assert white_moves[0].is_capture is True


def test_wait_does_not_record_incomplete_move():
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 5))
    engine.wait(2000)  # travel takes 5000ms, so the move hasn't landed yet

    assert engine.move_history.get_white_moves() == []


def test_snapshot_exposes_engine_move_history():
    board, rook = _board_with_rook()
    engine = GameEngine(board)

    engine.request_move(Position(0, 0), Position(0, 5))
    engine.wait(5000)

    snapshot = engine.snapshot()

    assert snapshot.move_history is engine.move_history
    assert len(snapshot.move_history.get_white_moves()) == 1
