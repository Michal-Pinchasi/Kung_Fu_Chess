import unittest
from position import Position

class TestPosition(unittest.TestCase):
    def test_position_initialization(self):
        """וידוא שנתוני השורה והעמודה נשמרים כראוי"""
        pos = Position(row=5, col=2)
        self.assertEqual(pos.row, 5)
        self.assertEqual(pos.col, 2)

if __name__ == "__main__":
    unittest.main()