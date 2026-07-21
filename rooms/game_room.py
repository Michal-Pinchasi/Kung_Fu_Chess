"""Membership, roles and state for one room; no WebSocket I/O."""

from dataclasses import dataclass
from enum import Enum
import time

from rooms.room_role import RoomRole


class RoomState(str, Enum):
    WAITING = "waiting_for_players"
    PLAYING = "playing"
    FINISHED = "finished"


@dataclass
class RoomMember:
    user: object
    role: RoomRole
    websocket: object | None
    joined_at: float


class GameRoom:
    def __init__(self, room_id: str, player_capacity: int, maximum_spectators: int,
                 clock=time.monotonic):
        self.room_id = room_id
        self.player_capacity = player_capacity
        self.maximum_spectators = maximum_spectators
        self.state = RoomState.WAITING
        self.game_id: str | None = None
        self._clock = clock
        self._members: dict[int, RoomMember] = {}

    def join(self, user, websocket) -> RoomMember:
        existing = self._members.get(user.id)
        if existing:
            existing.websocket = websocket
            return existing
        role = self._next_role()
        member = RoomMember(user, role, websocket, self._clock())
        self._members[user.id] = member
        return member

    def _next_role(self) -> RoomRole:
        roles = {member.role for member in self._members.values()}
        if RoomRole.WHITE not in roles:
            return RoomRole.WHITE
        if RoomRole.BLACK not in roles and self.player_capacity >= 2:
            return RoomRole.BLACK
        if self.spectator_count() >= self.maximum_spectators:
            raise ValueError("room_full")
        return RoomRole.SPECTATOR

    def member(self, user_id: int) -> RoomMember | None:
        return self._members.get(user_id)

    def role_for(self, user_id: int) -> RoomRole | None:
        member = self.member(user_id)
        return member.role if member else None

    def players(self) -> tuple[RoomMember, ...]:
        return tuple(member for member in self._members.values() if member.role.can_play)

    def spectators(self) -> tuple[RoomMember, ...]:
        return tuple(member for member in self._members.values() if member.role == RoomRole.SPECTATOR)

    def spectator_count(self) -> int:
        return len(self.spectators())

    def ready(self) -> bool:
        return len(self.players()) == self.player_capacity

    def disconnect(self, user_id: int) -> RoomMember | None:
        member = self.member(user_id)
        if member:
            member.websocket = None
        return member

    def leave(self, user_id: int) -> RoomMember | None:
        return self._members.pop(user_id, None)

    def reconnect(self, user_id: int, websocket) -> RoomMember:
        member = self._members[user_id]
        member.websocket = websocket
        return member

    def connections(self) -> tuple[object, ...]:
        return tuple(member.websocket for member in self._members.values() if member.websocket is not None)

    def members(self) -> tuple[RoomMember, ...]:
        return tuple(self._members.values())

    def members_payload(self) -> list[dict]:
        return [{"username": member.user.username, "rating": member.user.rating,
                 "role": member.role.value, "connected": member.websocket is not None}
                for member in self._members.values()]
