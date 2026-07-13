from model.board import Board
from typing import List


class GameState:
    """Holds the mutable application-level state of a running game."""

    def __init__(self, board: Board):
        self.board = board
        self.is_game_over = False
        self.winner = None


class MoveResult:
    """The official response object returned by GameEngine for any move request."""

    def __init__(self, is_accepted: bool, reason: str):
        self.is_accepted = is_accepted
        self.reason = reason


class PieceSnapshot:
    """An immutable read-only snapshot of a single piece, used by the renderer."""

    def __init__(self, id: str, kind: str, color: str, x: float, y: float, state: str):
        self.id = id
        self.kind = kind
        self.color = color
        self.x = x        # Pixel x position for interpolated rendering
        self.y = y        # Pixel y position for interpolated rendering
        self.state = state  # idle | moving | captured


class GameSnapshot:
    """An immutable read-only snapshot of the full game state, used by the renderer."""

    def __init__(
        self,
        board_width: int,
        board_height: int,
        pieces: List[PieceSnapshot],
        selected_cell,
        game_over: bool,
    ):
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces
        self.selected_cell = selected_cell
        self.game_over = game_over
