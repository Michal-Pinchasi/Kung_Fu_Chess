"""Client connection lifecycle states shared by networking and rendering."""

from enum import Enum


class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    LOBBY = "lobby"
    IN_ROOM = "in_room"
    SEARCHING = "searching"
    PLAYING = "playing"
    SPECTATING = "spectating"
    RECONNECTING = "reconnecting"
    GAME_OVER = "game_over"
    CLOSED = "closed"
