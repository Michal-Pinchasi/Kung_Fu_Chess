from model.position import Position

class Board:
    def __init__(self, width: int, height: int):
        self.width = width   # אחסון רוחב
        self.height = height # אחסון גובה
        # הלוח מאותחל כמערך של משבצות ריקות (".")
        self.grid = [["." for _ in range(width)] for _ in range(height)]

    def is_valid_position(self, row: int, col: int) -> bool:
        """בדיקה האם תא נמצא בגבולות הלוח"""
        return 0 <= row < self.height and 0 <= col < self.width

    def get_piece(self, row: int, col: int):
        """שאילתת כלי בתא"""
        if not self.is_valid_position(row, col):
            return "."
        return self.grid[row][col]

    def add_piece(self, row: int, col: int, piece) -> bool:
        """
        הוספת כלי ודחיית תפוסה כפולה!
        אם המשבצת כבר תפוסה על ידי כלי אחר, הפעולה תיכשל (תחזיר False).
        """
        if not self.is_valid_position(row, col):
            return False
        
        # דחיית תפוסה כפולה: מותר להוסיף רק אם המשבצת ריקה (".")
        if self.grid[row][col] != ".":
            return False
            
        self.grid[row][col] = piece
        if piece is not None and piece != ".":
            piece.cell = Position(row, col) # עדכון המיקום הפנימי של הכלי
        return True

    def remove_piece(self, row: int, col: int):
        """הסרת כלי מהלוח"""
        if self.is_valid_position(row, col):
            self.grid[row][col] = "."

    def move_piece(self, source: Position, destination: Position):
        """
        הזזת כלי לאחר שמהלך אומת!
        הפונקציה הזו מניחה שהאימות כבר קרה מחוץ ללוח.
        היא לא קוראת ל-RuleEngine, אלא פשוט מעבירה עיוורת את הכלי מהמקור ליעד.
        """
        if not self.is_valid_position(source.row, source.col) or not self.is_valid_position(destination.row, destination.col):
            return

        piece = self.get_piece(source.row, source.col)
        if piece == ".":
            return # אין כלי במקור להזיז

        # ביצוע המהלך הסטטי על הלוח:
        self.remove_piece(source.row, source.col) # פינוי המקור
        self.grid[destination.row][destination.col] = piece # השמה ביעד
        
        if hasattr(piece, 'cell'):
            piece.cell = destination # עדכון המיקום הלוגי החדש של הכלי