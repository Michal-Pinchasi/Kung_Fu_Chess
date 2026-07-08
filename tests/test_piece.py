import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from entities.piece import Piece
from entities.position import Position


class TestPiece(unittest.TestCase):
    def test_piece_initialization_and_forwarding(self):
        """is_legal_shape מעביר את הקריאה לאסטרטגיה ומחזיר את תוצאתה."""
        dummy_strategy = lambda from_pos, to_pos, board=None, piece=None: True

        piece = Piece(color="w", role="K", move_strategy=dummy_strategy)
        self.assertEqual(piece.color, "w")
        self.assertEqual(piece.role, "K")

        p1 = Position(0, 0)
        p2 = Position(1, 1)
        self.assertTrue(piece.is_legal_shape(p1, p2))

    def test_piece_forwards_board_to_strategy(self):
        """is_legal_shape מעביר את board לאסטרטגיה כשמסופק."""
        received = {}

        def capturing_strategy(from_pos, to_pos, board=None, piece=None):
            received['board'] = board
            return True

        piece = Piece(color="b", role="R", move_strategy=capturing_strategy)
        sentinel_board = object()  # אובייקט שרירותי כ"לוח"
        piece.is_legal_shape(Position(0, 0), Position(0, 3), board=sentinel_board)

        self.assertIs(received['board'], sentinel_board)

    def test_piece_without_board_still_works(self):
        """קריאה ל-is_legal_shape ללא board לא קורסת."""
        dummy_strategy = lambda from_pos, to_pos, board=None, piece=None: False
        piece = Piece(color="w", role="N", move_strategy=dummy_strategy)
        self.assertFalse(piece.is_legal_shape(Position(0, 0), Position(1, 2)))


if __name__ == "__main__":
    unittest.main()
