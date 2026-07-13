from model.position import Position
from config.constants import CELL_SIZE

class BoardMapper:
    @staticmethod
    def pixel_to_cell(x: int, y: int, width: int, height: int) -> Position or None:
        """
        מתרגם קואורדינטות מסך (פיקסלים) למיקום לוח לוגי (Position).
        אם הלחיצה מחוץ לגבולות הלוח, מחזיר None.
        """
        col = x // CELL_SIZE
        row = y // CELL_SIZE

        # בדיקה האם המיקום חורג מגבולות הלוח שסופקו
        if 0 <= row < height and 0 <= col < width:
            return Position(row, col)

        return None