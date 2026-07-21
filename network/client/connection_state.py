"""Client connection lifecycle states shared by networking and rendering."""

from enum import Enum


class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    LOBBY = "lobby"
    SEARCHING = "searching"
    PLAYING = "playing"
    RECONNECTING = "reconnecting"
    GAME_OVER = "game_over"
    CLOSED = "closed"
