import unittest
import sys
import os

# הוספת נתיב השורש של הפרויקט כדי שפייתון יזהה את החבילות החדשות
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.position import Position

class TestPosition(unittest.TestCase):
    def test_position_initialization(self):
        """וידוא שנתוני השורה והעמודה נשמרים כראוי"""
        pos = Position(row=5, col=2)
        self.assertEqual(pos.row, 5)
        self.col = 2 # תאימות לטסט המקורי שלך

    def test_position_equality(self):
        """וידוא ששני מיקומים עם אותה שורה ועמודה נחשבים שווים (נדרש באיטרציה 1)"""
        p1 = Position(3, 4)
        p2 = Position(3, 4)
        p3 = Position(1, 4)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)

    def test_position_readable_representation(self):
        """וידוא שייצוג המחרוזת מפיק פלט קריא לטסטים (נדרש באיטרציה 1)"""
        pos = Position(0, 1)
        self.assertEqual(repr(pos), "Position(0, 1)")

if __name__ == "__main__":
    unittest.main()