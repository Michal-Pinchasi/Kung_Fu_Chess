import unittest
import sys
import os

# הוספת נתיב השורש של הפרויקט כדי שפייתון ימצא את תיקיית model
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind

class TestPiece(unittest.TestCase):
    
    def test_piece_initialization_with_enums(self):
        """וידוא שהכלי מאותחל בהצלחה בעזרת ה-Enums מהדף הנפרד (איטרציה 1)"""
        pos = Position(0, 0)
        # יצירת כלי עם ה-Enums החדשים והגמישים שלנו
        piece = Piece(piece_id="wR_1", color=PieceColor.WHITE, kind=PieceKind.ROOK, cell=pos)
        
        # בדיקה שכל הנתונים נשמרו במדויק
        self.assertEqual(piece.id, "wR_1")
        self.assertEqual(piece.color, PieceColor.WHITE)
        self.assertEqual(piece.kind, PieceKind.ROOK)
        self.assertEqual(piece.cell, pos)
        self.assertEqual(piece.state, "idle") # מצב התחלתי תמיד חייב להיות idle

    def test_piece_state_lifecycle(self):
        """וידוא שמצב מחזור החיים משתנה בצורה תקינה במהלך המשחק (איטרציה 1)"""
        piece = Piece(piece_id="bP_1", color=PieceColor.BLACK, kind=PieceKind.PAWN)
        
        # כשהכלי מתחיל לזוז בזמן אמת, המצב שלו ישתנה ל-moving
        piece.state = "moving"
        self.assertEqual(piece.state, "moving")
        
        # כשהכלי נאכל על ידי היריב, המצב שלו ישתנה ל-captured
        piece.state = "captured"
        self.assertEqual(piece.state, "captured")

if __name__ == "__main__":
    unittest.main()