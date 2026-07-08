class Piece:
    def __init__(self, color: str, role: str, move_strategy):
        self.color = color             # "w" או "b"
        self.role = role               # "K", "R", "B", "Q", "N"
        self._move_strategy = move_strategy  # פונקציית האסטרטגיה המוזרקת

    def is_legal_shape(self, from_pos, to_pos, board=None) -> bool:
        """קריאה לאסטרטגיה שמוצמדת לכלי כדי לבדוק גיאומטריה ומסלול"""
        return self._move_strategy(from_pos, to_pos, board)