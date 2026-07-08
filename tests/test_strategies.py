import unittest
from entities.position import Position
from entities.strategies import (
    king_move_strategy, rook_move_strategy, bishop_strategy, 
    queen_strategy, knight_strategy
)

class TestStrategies(unittest.TestCase):
    def setUp(self):
        self.center = Position(2, 2)

    def test_king_strategy(self):
        # מהלך חוקי (צעד אחד לכל כיוון)
        self.assertTrue(king_move_strategy(self.center, Position(2, 3)))
        self.assertTrue(king_move_strategy(self.center, Position(3, 3)))
        # מהלך לא חוקי (שני צעדים)
        self.assertFalse(king_move_strategy(self.center, Position(2, 4)))

    def test_rook_strategy(self):
        # מהלכים חוקיים (קווים ישרים)
        self.assertTrue(rook_move_strategy(self.center, Position(2, 5)))
        self.assertTrue(rook_move_strategy(self.center, Position(0, 2)))
        # מהלך לא חוקי (אלכסון)
        self.assertFalse(rook_move_strategy(self.center, Position(3, 3)))

    def test_bishop_strategy(self):
        # מהלך חוקי (אלכסון מדויק)
        self.assertTrue(bishop_strategy(self.center, Position(4, 4)))
        self.assertTrue(bishop_strategy(self.center, Position(0, 4)))
        # מהלך לא חוקי (קו ישר או תנועה עקומה)
        self.assertFalse(bishop_strategy(self.center, Position(2, 3)))

    def test_queen_strategy(self):
        # מהלכים חוקיים (ישר ואלכסון)
        self.assertTrue(queen_strategy(self.center, Position(2, 5)))
        self.assertTrue(queen_strategy(self.center, Position(4, 4)))
        # מהלך לא חוקי (תנועת פרש למשל)
        self.assertFalse(queen_strategy(self.center, Position(4, 3)))

    def test_knight_strategy(self):
        # מהלכים חוקיים (צורת L: 2 ו-1)
        self.assertTrue(knight_strategy(self.center, Position(4, 3)))
        self.assertTrue(knight_strategy(self.center, Position(3, 4)))
        # מהלך לא חוקי (צעד ישר)
        self.assertFalse(knight_strategy(self.center, Position(2, 4)))

if __name__ == "__main__":
    unittest.main()