from enum import Enum


class RoomRole(str, Enum):
    WHITE = "white"
    BLACK = "black"
    SPECTATOR = "spectator"

    @property
    def can_play(self) -> bool:
        return self in (RoomRole.WHITE, RoomRole.BLACK)

    @property
    def color_value(self) -> str | None:
        return {RoomRole.WHITE: "w", RoomRole.BLACK: "b"}.get(self)
