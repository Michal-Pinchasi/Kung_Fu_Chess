from model.position import Position

class BoardMapper:
    CELL_SIZE = 100 # קבוע הפיקסלים לפי הנחיות ה-Word

    @staticmethod
    def pixel_to_cell(x: int, y: int, width: int, height: int) -> Position or None:
        """
        מתרגם קואורדינטות מסך (פיקסלים) למיקום לוח לוגי (Position).
        אם הלחיצה מחוץ לגבולות הלוח, מחזיר None.
        """
        col = x // BoardMapper.CELL_SIZE
        row = y // BoardMapper.CELL_SIZE
        
        # בדיקה האם המיקום חורג מגבולות הלוח שסופקו
        if 0 <= row < height and 0 <= col < width:
            return Position(row, col)
            
        return None