"""Secure room creation and indexed room lookup."""

import secrets

from rooms.game_room import GameRoom


class RoomManager:
    def __init__(self, settings):
        self.settings = settings
        self._rooms: dict[str, GameRoom] = {}
        self._by_user: dict[int, str] = {}
        self._by_game: dict[str, str] = {}

    def create(self, user, websocket) -> tuple[GameRoom, object]:
        if user.id in self._by_user:
            raise ValueError("already_in_room")
        room_id = self._unique_id()
        room = GameRoom(room_id, self.settings.player_capacity, self.settings.maximum_spectators)
        self._rooms[room_id] = room
        member = room.join(user, websocket)
        self._by_user[user.id] = room_id
        return room, member

    def join(self, room_id: str, user, websocket) -> tuple[GameRoom, object]:
        if user.id in self._by_user:
            raise ValueError("already_in_room")
        room = self._rooms.get(room_id.strip().upper())
        if room is None:
            raise ValueError("room_not_found")
        member = room.join(user, websocket)
        self._by_user[user.id] = room.room_id
        return room, member

    def create_for_match(self, first, second) -> GameRoom:
        room, _ = self.create(first.user, first.websocket)
        self.join(room.room_id, second.user, second.websocket)
        return room

    def get(self, room_id: str) -> GameRoom | None:
        return self._rooms.get(room_id.strip().upper())

    def for_user(self, user_id: int) -> GameRoom | None:
        room_id = self._by_user.get(user_id)
        return self._rooms.get(room_id) if room_id else None

    def for_game(self, game_id: str) -> GameRoom | None:
        room_id = self._by_game.get(game_id)
        return self._rooms.get(room_id) if room_id else None

    def attach_game(self, room_id: str, game_id: str) -> None:
        room = self.get(room_id)
        room.game_id = game_id
        self._by_game[game_id] = room.room_id

    def leave(self, user_id: int):
        room = self.for_user(user_id)
        if room is None:
            return None
        member = room.leave(user_id)
        self._by_user.pop(user_id, None)
        if not room.connections():
            self._rooms.pop(room.room_id, None)
            if room.game_id:
                self._by_game.pop(room.game_id, None)
        return member

    def _unique_id(self) -> str:
        while True:
            room_id = secrets.token_urlsafe(self.settings.room_id_bytes).replace("-", "").replace("_", "").upper()
            if room_id not in self._rooms:
                return room_id
