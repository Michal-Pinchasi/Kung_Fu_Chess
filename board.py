class Board:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [["." for _ in range(width)] for _ in range(height)]

    def set_piece(self, row: int, col: int, piece_text: str):
        self.grid[row][col] = piece_text

    def get_piece(self, row: int, col: int) -> str:
        return self.grid[row][col]