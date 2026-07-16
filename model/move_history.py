from typing import List, NamedTuple
from model.position import Position


class Move(NamedTuple):
    """A single move record."""
    source: Position
    destination: Position
    piece_kind: str  # 'K', 'Q', 'R', 'N', 'B', 'P'
    is_capture: bool


class MoveHistory:
    """Tracks all moves made by each player."""

    def __init__(self):
        self.white_moves: List[Move] = []
        self.black_moves: List[Move] = []

    def add_move(self, color: str, source: Position, destination: Position, piece_kind: str, is_capture: bool) -> None:
        """Record a move by a player.
        
        Parameters
        ----------
        color : str
            'w' for white, 'b' for black
        source : Position
            Starting position
        destination : Position
            Ending position
        piece_kind : str
            Piece type: 'K', 'Q', 'R', 'N', 'B', 'P'
        is_capture : bool
            Whether the move resulted in a capture
        """
        move = Move(source, destination, piece_kind, is_capture)
        if color == 'w':
            self.white_moves.append(move)
        else:
            self.black_moves.append(move)

    def get_white_moves(self) -> List[Move]:
        """Return all white moves."""
        return self.white_moves.copy()

    def get_black_moves(self) -> List[Move]:
        """Return all black moves."""
        return self.black_moves.copy()

    def clear(self) -> None:
        """Clear all move history."""
        self.white_moves.clear()
        self.black_moves.clear()
