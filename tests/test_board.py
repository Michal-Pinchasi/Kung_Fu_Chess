import unittest
from entities.board import Board

class TestBoard(unittest.TestCase):
    def test_board_initialization(self):
        """בדיקת אתחול לוח ריק בגודל דינמי"""
        board = Board(width=4, height=3)
        self.assertEqual(board.width, 4)
        self.assertEqual(board.height, 3)
        # וידוא שכל המשבצות אותחלו כנקודות
        for r in range(3):
            for c in range(4):
                self.assertEqual(board.grid[r][c], ".")

    def test_is_valid_position(self):
        """בדיקת גבולות הלוח - מקרי קצה פנימה והחוצה"""
        board = Board(width=3, height=2)
        
        # מיקומים תקינים
        self.assertTrue(board.is_valid_position(0, 0))
        self.assertTrue(board.is_valid_position(1, 2))
        
        # מיקומים לא תקינים (חריגה מלמעלה, למטה, וערכים שליליים)
        self.assertFalse(board.is_valid_position(-1, 0))
        self.assertFalse(board.is_valid_position(0, -1))
        self.assertFalse(board.is_valid_position(2, 0))  # גובה הוא 2, אינדקס מקסימלי 1
        self.assertFalse(board.is_valid_position(0, 3))  # רוחב הוא 3, אינדקס מקסימלי 2

    def test_get_and_set_piece_valid(self):
        """בדיקת השמה וקריאה בתוך גבולות הלוח"""
        board = Board(width=3, height=3)
        board.set_piece(1, 2, "wK")
        self.assertEqual(board.get_piece(1, 2), "wK")

    def test_get_and_set_piece_invalid_bounds(self):
        """וידוא הגנה מחוץ לגבולות הלוח (אינקפסולציה)"""
        board = Board(width=3, height=3)
        
        # השמה מחוץ ללוח לא אמורה לקרוס
        board.set_piece(5, 5, "bQ") 
        
        # קריאה מחוץ ללוח מחזירה נקודה ולא קורסת
        self.assertEqual(board.get_piece(5, 5), ".")

if __name__ == "__main__":
    unittest.main()