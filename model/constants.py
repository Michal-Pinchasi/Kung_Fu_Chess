from enum import Enum


class PieceColor(Enum):
    """Enum for the two piece colors used in the game."""
    WHITE = "w"
    BLACK = "b"


class PieceKind(Enum):
    """Enum for all supported piece types."""
    KING = "K"
    QUEEN = "Q"
    ROOK = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN = "P"
