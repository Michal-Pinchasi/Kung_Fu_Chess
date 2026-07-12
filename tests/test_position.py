import unittest
from model.position import Position

class TestPosition(unittest.TestCase):
    def test_position_initialization(self):
        """וידוא שנתוני השורה והעמודה נשמרים כראוי"""
        pos = Position(row=5, col=2)
        self.assertEqual(pos.row, 5)
        self.assertEqual(pos.col, 2)  # תוקן מ-self.col = 2

    def test_position_equality(self):
        p1 = Position(3, 4)
        p2 = Position(3, 4)
        p3 = Position(1, 4)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        self.assertNotEqual(p1, "not_a_position")  # מוודא השוואה מול סוגים אחרים

    def test_position_readable_representation(self):
        pos = Position(0, 1)
        self.assertEqual(repr(pos), "Position(0, 1)")

if __name__ == "__main__":
    unittest.main()