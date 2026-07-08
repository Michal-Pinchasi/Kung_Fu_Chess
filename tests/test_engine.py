import unittest
import sys
import os

# הוספת נתיב השורש כדי שפייתון ימצא את תיקיית entities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from entities.board import Board
from entities.piece import Piece
from entities.strategies import STRATEGIES_MAP
from engine import GameEngine

class TestGameEngine(unittest.TestCase):
    def setUp(self):
        """הקמת סביבה נקייה עם אובייקטים אמיתיים של Piece לכל טסט"""
        self.board = Board(width=3, height=3)
        
        self.white_king = Piece("w", "K", STRATEGIES_MAP["K"])
        self.black_rook = Piece("b", "R", STRATEGIES_MAP["R"])
        
        self.board.set_piece(0, 0, self.white_king)
        self.board.set_piece(0, 2, self.black_rook)
        
        self.engine = GameEngine(self.board)

    def test_click_outside_board_ignored(self):
        self.engine.handle_click(500, 500)
        self.assertIsNone(self.engine.selected_pos)

    def test_click_to_select_piece(self):
        self.engine.handle_click(50, 50)  # משבצת (0,0) - מלך לבן
        self.assertEqual(self.engine.selected_pos.row, 0)
        self.assertEqual(self.engine.selected_pos.col, 0)

    def test_legal_move_executed(self):
        """מלך זז צעד אחד הצידה - מהלך גיאומטרי חוקי, הכלי נכנס לאוויר"""
        self.engine.handle_click(50, 50)   # בחירת המלך ב-(0,0)
        self.engine.handle_click(150, 50)  # לחיצה על (0,1) - צעד חוקי למלך
        
        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(len(self.engine.active_moves), 1)

    def test_illegal_move_shape_ignored(self):
        """מלך מנסה לזוז שני צעדים הצידה - לא חוקי, המהלך מבוטל והבחירה מתאפסת"""
        self.engine.handle_click(50, 50)   # בחירת המלך ב-(0,0)
        self.engine.handle_click(250, 50)  # לחיצה על (0,2) - שני צעדים (אסור!)
        
        # המלך נשאר במקומו, שום מהלך לא באוויר, והבחירה התאפסה
        self.assertEqual(self.board.get_piece(0, 0), self.white_king)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNone(self.engine.selected_pos)

    def test_advance_time_completes_move(self):
        self.engine.handle_click(50, 50)
        self.engine.handle_click(150, 50)  # מהלך חוקי
        
        self.engine.advance_time(1000)
        self.assertEqual(self.board.get_piece(0, 1), self.white_king)
        self.assertEqual(len(self.engine.active_moves), 0)

if __name__ == "__main__":
    unittest.main()