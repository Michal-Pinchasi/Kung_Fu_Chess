from entities.position import Position

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

    def set_piece(self, row: int, col: int, piece):
        if self.is_valid_position(row, col):
            self.grid[row][col] = piece