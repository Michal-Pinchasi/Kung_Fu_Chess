"""
Tracks connected multiplayer clients and assigns each a player color.

The first client to connect is assigned WHITE, the second BLACK. Further
connections are rejected — spectator support is a future extension, not
part of Phase 1. Also enforces that a client may only command pieces of
its own assigned color, checked against the live board rather than any
color the client itself claims.
"""

from typing import Dict, Optional
from model.position import Position
from model.constants import PieceColor
from config.config_loader import EMPTY_SQUARE


class SessionManager:
    """Assigns player colors to connected clients and authorizes their commands.

    A "connection" is any hashable object that uniquely identifies a client
    (e.g. a websockets ServerConnection). This class has no knowledge of
    WebSockets or networking at all — only of the color-assignment and
    ownership-authorization rules, so it can be unit-tested with plain
    placeholder objects standing in for real connections.
    """

    #: Maximum number of simultaneous players this session supports (Phase 1: local 1v1).
    MAX_PLAYERS = 2

    def __init__(self) -> None:
        """Initialize a session with no connected clients."""
        self._assignments: Dict[object, PieceColor] = {}

    def assign_color(self, connection) -> Optional[PieceColor]:
        """Assign the next available player color to connection.

        Returns PieceColor.WHITE for the first connection, PieceColor.BLACK
        for the second. Reconnecting the same connection object returns its
        existing assignment unchanged. Returns None when two players are
        already connected and connection is a new one (the session is full).
        """
        if connection in self._assignments:
            return self._assignments[connection]

        if len(self._assignments) >= self.MAX_PLAYERS:
            return None

        assigned_colors = set(self._assignments.values())
        color = PieceColor.WHITE if PieceColor.WHITE not in assigned_colors else PieceColor.BLACK
        self._assignments[connection] = color
        return color

    def color_for(self, connection) -> Optional[PieceColor]:
        """Return the color previously assigned to connection, or None if unassigned."""
        return self._assignments.get(connection)

    def release(self, connection) -> None:
        """Free connection's color slot, e.g. when the client disconnects.

        Silently does nothing if connection was never assigned a color.
        """
        self._assignments.pop(connection, None)

    def is_full(self) -> bool:
        """Return True when MAX_PLAYERS clients are already connected."""
        return len(self._assignments) >= self.MAX_PLAYERS

    def is_authorized(self, connection, board, source: Position) -> bool:
        """Return True when connection may command the piece currently at source.

        Authorization is always derived from the live board occupancy at
        source, never from any color a client claims in a wire command —
        board state is the only source of truth for legality anywhere in
        this codebase (the same principle RuleEngine and SessionManager's
        sibling classes already follow). Returns False when connection has
        no color assignment, or when source is empty.
        """
        color = self.color_for(connection)
        if color is None:
            return False

        piece = board.get_piece(source.row, source.col)
        if piece == EMPTY_SQUARE or piece is None:
            return False

        return piece.color == color
