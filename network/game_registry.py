"""Creation and lookup of independent active game sessions."""

import secrets
from storage.board_parser import BoardParser
from engin.game_engine import GameEngine
from events.message_bus import MessageBus
from network.game_session import GameSession


class GameRegistry:
    def __init__(self, board_text: str, id_bytes: int = 12, event_auditor=None):
        self.board_text = board_text
        self.id_bytes = id_bytes
        self._games: dict[str, GameSession] = {}
        self._by_user: dict[int, str] = {}
        self.event_auditor = event_auditor

    def create(self, white, black, white_socket, black_socket) -> GameSession:
        game_id = secrets.token_urlsafe(self.id_bytes)
        bus = MessageBus()
        if self.event_auditor:
            self.event_auditor.attach(bus, game_id)
        engine = GameEngine(BoardParser.parse(self.board_text), message_bus=bus)
        game = GameSession(game_id, engine, white, black, white_socket, black_socket, bus)
        self._games[game_id] = game
        self._by_user[white.id] = game_id
        self._by_user[black.id] = game_id
        return game

    def get(self, game_id: str) -> GameSession | None:
        return self._games.get(game_id)

    def for_user(self, user_id: int) -> GameSession | None:
        game_id = self._by_user.get(user_id)
        return self._games.get(game_id) if game_id else None

    def remove(self, game_id: str) -> GameSession | None:
        game = self._games.pop(game_id, None)
        if game:
            for user_id in game.players:
                self._by_user.pop(user_id, None)
        return game

    def all(self) -> tuple[GameSession, ...]:
        return tuple(self._games.values())
