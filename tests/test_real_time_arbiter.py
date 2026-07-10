import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from realtime.real_time_arbiter import RealTimeArbiter

class TestRealTimeArbiter(unittest.TestCase):

    def setUp(self):
        self.board = Board(width=4, height=4)
        self.arbiter = RealTimeArbiter(self.board)
        
        self.white_rook = Piece("wR_1", PieceColor.WHITE, PieceKind.ROOK)
        self.black_king = Piece("bK_1", PieceColor.BLACK, PieceKind.KING)
        self.white_pawn = Piece("wP_1", PieceColor.WHITE, PieceKind.PAWN)

        self.board.add_piece(0, 0, self.white_rook)
        self.board.add_piece(0, 3, self.black_king)

    def test_start_motion_updates_state(self):
        """1. וידוא שתחילת תנועה רושמת אותה בבורר ומעדכנת את מצב הכלי ל-moving"""
        self.arbiter.start_motion(self.white_rook, Position(0, 0), Position(0, 2), duration_ticks=5)
        
        self.assertEqual(len(self.arbiter.active_motions), 1)
        self.assertEqual(self.white_rook.state, "moving")

    def test_has_motion_on_path(self):
        """2. וידוא שזיהוי מסלול תפוס באוויר עובד עבור קואורדינטות מקור או יעד"""
        self.arbiter.start_motion(self.white_rook, Position(0, 0), Position(0, 2), duration_ticks=5)
        
        # בדיקה על אותה משבצת מקור
        self.assertTrue(self.arbiter.has_motion_on_path(Position(0, 0), Position(1, 0)))
        # בדיקה על משבצת יעד שכבר מיועדת לכלי אחר באוויר
        self.assertTrue(self.arbiter.has_motion_on_path(Position(2, 2), Position(0, 2)))
        # בדיקה על מסלול פנוי לחלוטין
        self.assertFalse(self.arbiter.has_motion_on_path(Position(3, 3), Position(3, 2)))

    def test_advance_time_completes_and_moves_piece(self):
        """3. וידוא שקידום זמן מספק מסיים את המהלך, מזיז את הכלי על הלוח ומחזיר אותו ל-idle"""
        self.arbiter.start_motion(self.white_rook, Position(0, 0), Position(0, 2), duration_ticks=2)
        
        # קידום זמן ב-200 מילישניות (שווה ל-2 Ticks)
        king_captured = self.arbiter.advance_time(200)
        
        self.assertFalse(king_captured)
        self.assertEqual(len(self.arbiter.active_motions), 0)
        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(self.board.get_piece(0, 2), self.white_rook)
        self.assertEqual(self.white_rook.state, "idle")

    def test_advance_time_detects_king_capture(self):
        """4. וידוא שקידום זמן המביא לדריסת מלך אויב מחזיר חיווי אכילת מלך"""
        self.arbiter.start_motion(self.white_rook, Position(0, 0), Position(0, 3), duration_ticks=1)
        
        king_captured = self.arbiter.advance_time(100) # 1 Tick
        self.assertTrue(king_captured)

    def test_friendly_collision_at_destination_cancels_move(self):
        """5. מקרה קצה: וידוא שאם כלי ידידותי תפס את משבצת היעד בזמן שהיינו באוויר, המהלך מבוטל בבטחה"""
        # נניח שהצריח יוצא לדרך אל (0,2) למשך 2 Ticks
        self.arbiter.start_motion(self.white_rook, Position(0, 0), Position(0, 2), duration_ticks=2)
        
        # בינתיים, כלי חבר (רגלי לבן) מונחת פיזית במשבצת היעד (0,2) באופן פתאומי
        self.board.add_piece(0, 2, self.white_pawn)
        
        # הזמן מתקדם והצריח מגיע ליעד
        self.arbiter.advance_time(200)
        
        # המהלך היה אמור להתבטל: הצריח נשאר פיזית ב-(0,0), והרגלי נשאר ב-(0,2)
        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(self.board.get_piece(0, 2), self.white_pawn)
        self.assertEqual(self.white_rook.state, "idle") # חזר למנוחה בבטחה

if __name__ == "__main__":
    unittest.main()