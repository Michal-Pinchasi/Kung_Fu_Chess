"""Runtime state and authorization for one active match."""

from dataclasses import dataclass
from events.game_events import GAME_OVER
from model.constants import PieceColor
from config.config_loader import EMPTY_SQUARE


@dataclass
class PlayerSlot:
    user: object
    color: PieceColor
    websocket: object | None


class GameSession:
    """Owns one engine and its two player slots; performs no persistence or I/O."""

    def __init__(self, game_id: str, engine, white, black, white_socket, black_socket, bus):
        self.game_id = game_id
        self.engine = engine
        self.sequence = 0
        self.finished = False
        self.result_applied = False
        self.pending_game_over = None
        self.players = {
            white.id: PlayerSlot(white, PieceColor.WHITE, white_socket),
            black.id: PlayerSlot(black, PieceColor.BLACK, black_socket),
        }
        bus.subscribe(GAME_OVER, self._capture_game_over)

    def _capture_game_over(self, event) -> None:
        self.pending_game_over = event

    def slot_for_user(self, user_id: int) -> PlayerSlot | None:
        return self.players.get(user_id)

    def slot_for_connection(self, websocket) -> PlayerSlot | None:
        return next((slot for slot in self.players.values() if slot.websocket is websocket), None)

    def opponent_of(self, user_id: int) -> PlayerSlot | None:
        return next((slot for uid, slot in self.players.items() if uid != user_id), None)

    def reconnect(self, user_id: int, websocket) -> PlayerSlot:
        slot = self.players[user_id]
        slot.websocket = websocket
        return slot

    def disconnect(self, user_id: int) -> None:
        self.players[user_id].websocket = None

    def is_authorized(self, user_id: int, source) -> bool:
        slot = self.slot_for_user(user_id)
        piece = self.engine.board.get_piece(source.row, source.col)
        return bool(slot and piece not in (None, EMPTY_SQUARE) and piece.color == slot.color)

    def tick(self, milliseconds: int) -> None:
        if not self.finished:
            self.engine.wait(milliseconds)

    def next_snapshot(self) -> tuple[int, object]:
        self.sequence += 1
        return self.sequence, self.engine.snapshot()
