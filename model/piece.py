class Piece:
    """Represents a single chess piece on the board.

    Holds identity, type, color, and lifecycle state.
    Does not contain movement logic, pixel coordinates, or timing data.
    """

    def __init__(self, id: str, kind, color):
        self.id = id        # Unique stable identifier, e.g. "wR_0"
        self.kind = kind    # PieceKind enum value (ROOK, PAWN, etc.)
        self.color = color  # PieceColor enum value (WHITE or BLACK)
        self.state = "idle" # Lifecycle flag: idle | moving | jump | long_rest | short_rest | captured
        self.cell = None    # Current board position (set externally)
