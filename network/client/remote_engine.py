"""Engine-shaped adapter that turns local UI clicks into server commands."""

from types import SimpleNamespace

from engin.game_engine import MoveResult
from input.controller import Controller
from model.game_state import GameSnapshot
from model.position import Position


class RemoteEngine:
    """The small GameEngine interface required by the existing GUI and Controller."""

    def __init__(self, client):
        self.client = client
        self.board = SimpleNamespace(width=8, height=8)
        self.game_state = SimpleNamespace(is_game_over=False)
        self.controller = Controller(self)

    def snapshot(self):
        snapshot = self.client.latest_snapshot()
        if snapshot is None:
            snapshot = GameSnapshot(8, 8, [], self.controller.selected_cell, False)
        else:
            # Selection is client-local UI state; the server never owns it.
            snapshot = GameSnapshot(snapshot.board_width, snapshot.board_height, snapshot.pieces,
                                    self.controller.selected_cell, snapshot.game_over,
                                    snapshot.move_history, snapshot.score)
        self.board.width, self.board.height = snapshot.board_width, snapshot.board_height
        self.game_state.is_game_over = snapshot.game_over
        return snapshot

    def is_cell_empty(self, position: Position) -> bool:
        piece = self._piece_at(position)
        # Do not allow selecting an opponent's piece; the server enforces this too.
        return piece is None or piece.color != self.client.color

    def is_friendly_piece(self, position: Position, reference: Position) -> bool:
        piece = self._piece_at(position)
        other = self._piece_at(reference)
        return piece is not None and other is not None and piece.color == other.color

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        piece = self._piece_at(source)
        if piece is None or piece.color != self.client.color:
            return MoveResult(False, "not_your_piece")
        return MoveResult(self.client.send_command(self._move_command(piece.kind, source, destination)))

    def request_jump(self, position: Position) -> MoveResult:
        piece = self._piece_at(position)
        if piece is None or piece.color != self.client.color:
            return MoveResult(False, "not_your_piece")
        return MoveResult(self.client.send_command(self._jump_command(piece.kind, position)))

    def wait(self, ms: int) -> None:
        """Compatibility no-op: the server alone advances game time."""

    def _piece_at(self, position):
        snapshot = self.client.latest_snapshot()
        if snapshot is None:
            return None
        for piece in snapshot.pieces:
            if round(piece.y) == position.row and round(piece.x) == position.col:
                return piece
        return None

    def _move_command(self, kind, source, destination) -> str:
        return f"{self._color_letter()}{kind}{self._square(source)}{self._square(destination)}"

    def _jump_command(self, kind, position) -> str:
        return f"{self._color_letter()}{kind}{self._square(position)}J"

    def _color_letter(self) -> str:
        return "W" if self.client.color == "w" else "B"

    @staticmethod
    def _square(position) -> str:
        return f"{chr(ord('a') + position.col)}{position.row + 1}"
