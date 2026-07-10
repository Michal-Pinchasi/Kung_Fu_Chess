import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from rules.rule_engine import RuleEngine

class TestRuleEngine(unittest.TestCase):

    def setUp(self):
        # הכנת לוח בדיקות בסיסי בגודל 4x4 לכל טסט
        self.board = Board(width=4, height=4)
        self.white_rook = Piece("wR_1", PieceColor.WHITE, PieceKind.ROOK)
        self.white_pawn = Piece("wP_1", PieceColor.WHITE, PieceKind.PAWN)
        self.black_king = Piece("bK_1", PieceColor.BLACK, PieceKind.KING)

        self.board.add_piece(0, 0, self.white_rook)
        self.board.add_piece(0, 2, self.white_pawn)
        self.board.add_piece(0, 3, self.black_king)

    def test_validate_move_empty_source(self):
        """1. וידוא שמהלך ממשבצת ריקה נפסל עם סיבה מתאימה"""
        validation = RuleEngine.validate_move(self.board, Position(2, 2), Position(2, 3))
        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.reason, "empty_source")

    def test_validate_move_outside_board(self):
        """2. וידוא שמהלך אל מחוץ לגבולות הלוח נפסל"""
        validation = RuleEngine.validate_move(self.board, Position(0, 0), Position(-1, 0))
        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.reason, "outside_board")

    def test_validate_move_friendly_destination(self):
        """3. וידוא שנפסל ניסיון אכילה של כלי ידידותי (באותו הצבע)"""
        # צריח לבן ב-(0,0) מנסה לנוע ל-(0,2) שבו יושב רגלי לבן
        validation = RuleEngine.validate_move(self.board, Position(0, 0), Position(0, 2))
        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.reason, "friendly_destination")

    def test_validate_move_illegal_piece_geometry(self):
        """4. וידוא שנפסל מהלך שאינו תואם את הגיאומטריה של הכלי (למשל צריח שנע באלכסון)"""
        validation = RuleEngine.validate_move(self.board, Position(0, 0), Position(1, 1))
        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.reason, "illegal_piece_move")

    def test_validate_move_legal_capture(self):
        """5. וידוא שמהלך אכילה של כלי אויב עם מסלול פנוי מאושר בהצלחה"""
        # נסיר זמנית את הרגלי הלבן שחוסם את הדרך אל המלך השחור
        self.board.remove_piece(0, 2)
        
        # צריח לבן ב-(0,0) אוכל מלך שחור ב-(0,3) - מסלול פנוי ויעד אויב
        validation = RuleEngine.validate_move(self.board, Position(0, 0), Position(0, 3))
        self.assertTrue(validation.is_valid)
        self.assertEqual(validation.reason, "ok")

if __name__ == "__main__":
    unittest.main()