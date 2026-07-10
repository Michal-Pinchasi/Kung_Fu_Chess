from enum import Enum

class PieceColor(Enum):
    """Enum גמיש לצבעי הכלים (WHITE / BLACK)"""
    WHITE = "w"
    BLACK = "b"

class PieceKind(Enum):
    """Enum גמיש לסוגי הכלים (KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN)"""
    KING = "K"
    QUEEN = "Q"
    ROOK = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN = "P"