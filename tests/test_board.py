import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from entities.board import Board
from entities.piece import Piece

class TestBoard(unittest.TestCase):
    def test_board_initialization(self):
        board = Board(width=4, height=3)
        self.assertEqual(board.width, 4)
        self.assertEqual(board.height, 3)
        for r in range(3):
            for c in range(4):
                self.assertEqual(board.grid[r][c], ".")

    def test_is_valid_position(self):
        board = Board(width=3, height=2)
        self.assertTrue(board.is_valid_position(0, 0))
        self.assertTrue(board.is_valid_position(1, 2))
        self.assertFalse(board.is_valid_position(-1, 0))
        self.assertFalse(board.is_valid_position(2, 0))

    def test_get_and_set_piece_valid(self):
        board = Board(width=3, height=3)
        # יוצרים אובייקט Piece אמיתי עם אסטרטגיה ריקה לצורך הטסט
        mock_piece = Piece("w", "K", lambda f, t: True)
        board.set_piece(1, 2, mock_piece)
        self.assertEqual(board.get_piece(1, 2), mock_piece)

    def test_get_and_set_piece_invalid_bounds(self):
        board = Board(width=3, height=3)
        mock_piece = Piece("b", "Q", lambda f, t: True)
        board.set_piece(5, 5, mock_piece) 
        self.assertEqual(board.get_piece(5, 5), ".")

if __name__ == "__main__":
    unittest.main()