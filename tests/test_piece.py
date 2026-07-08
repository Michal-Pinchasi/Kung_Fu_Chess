import unittest
from entities.piece import Piece
from entities.position import Position

class TestPiece(unittest.TestCase):
    def test_piece_initialization_and_forwarding(self):
        # יצירת אסטרטגיית דמה (Mock Strategy) שמחזירה תמיד True
        dummy_strategy = lambda from_pos, to_pos: True
        
        piece = Piece(color="w", role="K", move_strategy=dummy_strategy)
        self.assertEqual(piece.color, "w")
        self.assertEqual(piece.role, "K")
        
        # וידוא שהקריאה ל-is_legal_shape מגיעה לאסטרטגיה ומחזירה True
        p1 = Position(0, 0)
        p2 = Position(1, 1)
        self.assertTrue(piece.is_legal_shape(p1, p2))

if __name__ == "__main__":
    unittest.main()