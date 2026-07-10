class Position:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
    def __eq__(self, other):
        """מאפשר להשוות בין שני מיקומים בעזרת האופרטור == (נדרש באיטרציה 1)"""
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __repr__(self):
        """מפיק ייצוג קריא להודעות שגיאה ברורות בבדיקות (נדרש באיטרציה 1)"""
        return f"Position({self.row}, {self.col})"