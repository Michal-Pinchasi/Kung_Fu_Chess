from model.position import Position

class Board:
    def __init__(self, width: int, height: int):
        self.width = width   
        self.height = height 
        self.grid = [["." for _ in range(width)] for _ in range(height)]

    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width

    def get_piece(self, row: int, col: int):
        if not self.is_valid_position(row, col):
            return "."
        return self.grid[row][col]

    def add_piece(self, row: int, col: int, piece) -> bool:
        if not self.is_valid_position(row, col):
            return False
        if self.grid[row][col] != ".":
            return False
        self.grid[row][col] = piece
        if piece is not None and piece != ".":
            piece.cell = Position(row, col)
        return True

    def remove_piece(self, row: int, col: int):
        if self.is_valid_position(row, col):
            self.grid[row][col] = "."

    def move_piece(self, source: Position, destination: Position):
        """הזזת כלי ועדכון מיקומו ומצבו בנחיתה הפיזית[cite: 1, 4]"""
        if not self.is_valid_position(source.row, source.col) or not self.is_valid_position(destination.row, destination.col):
            return

        piece = self.get_piece(source.row, source.col)
        if piece == ".":
            return 

        self.remove_piece(source.row, source.col)
        self.grid[destination.row][destination.col] = piece
        
        if hasattr(piece, 'cell'):
            piece.cell = destination
            
        # עדכון מצב הכלי חזרה למנוחה עם נחיתתו[cite: 4]
        if hasattr(piece, 'state'):
            piece.state = "idle"
    def set_piece(self, row: int, col: int, piece):
        """מציב כלי ישירות במשבצת (משמש לנחיתה מהאוויר או עדכון ישיר)"""
        if self.is_valid_position(row, col):
            self.grid[row][col] = piece
            if piece is not None and piece != ".":
                piece.cell = Position(row, col)
                piece.state = "idle"