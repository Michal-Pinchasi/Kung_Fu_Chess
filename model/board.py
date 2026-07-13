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
        return True

    def remove_piece(self, row: int, col: int):
        if self.is_valid_position(row, col):
            self.grid[row][col] = "."

    def set_piece(self, row: int, col: int, piece):
        """השמה ישירה של כלי במשבצת (נדרש על ידי ה-Arbiter בזמן נחיתה)"""
        if self.is_valid_position(row, col):
            self.grid[row][col] = piece

    def move_piece(self, source: Position, destination: Position):
        if not self.is_valid_position(source.row, source.col) or not self.is_valid_position(destination.row, destination.col):
            return

        piece = self.get_piece(source.row, source.col)
        if piece == ".":
            return 

        self.remove_piece(source.row, source.col)
        self.grid[destination.row][destination.col] = piece