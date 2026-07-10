from model.position import Position
from model.constants import PieceColor, PieceKind

class Piece:
    def __init__(self, piece_id: str, color: PieceColor, kind: PieceKind, cell: Position = None):
        self.id = piece_id          # מזהה ייחודי קבוע (wR_1)
        self.color = color          # צבע (PieceColor.WHITE / BLACK)
        self.kind = kind            # סוג (PieceKind.ROOK וכו')
        self.cell = cell            # מיקום לוגי על הלוח
        self.state = "idle"         # מצב מחזור חיים: idle, moving, captured