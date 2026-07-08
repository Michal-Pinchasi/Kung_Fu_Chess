class Board:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [["." for _ in range(width)] for _ in range(height)]

    def set_piece(self, row: int, col: int, piece_text: str):
        if self.is_valid_position(row, col):
            self.grid[row][col] = piece_text

    def get_piece(self, row: int, col: int) -> str:
        if self.is_valid_position(row, col):
            return self.grid[row][col]
        return "."

    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < self.height and 0 <= col < self.width