import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from Kung_Fu_Chess.realtime.motion import Motion

class TestMotionLifecycle(unittest.TestCase):
    def test_motion_lifecycle_ticks(self):
        """וידוא שהתנועה מנהלת את הזמן הנותר בצורה תקינה ומזהה סיום מהלך"""
        piece = Piece("wR_1", PieceColor.WHITE, PieceKind.ROOK)
        source = Position(0, 0)
        destination = Position(0, 3)
        
        # יצירת תנועה שלוקחת 2 פעימות זמן (Ticks)
        motion = Motion(piece, source, destination, duration_ticks=2)
        
        self.assertFalse(motion.is_finished())
        self.assertEqual(motion.remaining_ticks, 2)
        
        # פעימה ראשונה
        motion.tick()
        self.assertFalse(motion.is_finished())
        self.assertEqual(motion.remaining_ticks, 1)
        
        # פעימה שנייה - ההגעה ליעד
        motion.tick()
        self.assertTrue(motion.is_finished())
        self.assertEqual(motion.remaining_ticks, 0)

if __name__ == "__main__":
    unittest.main()