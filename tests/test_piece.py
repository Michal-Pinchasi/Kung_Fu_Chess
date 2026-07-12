import unittest
from model.piece import Piece
from model.constants import PieceColor, PieceKind

class TestPiece(unittest.TestCase):
    
    def test_piece_initialization_with_enums(self):
        """וידוא שהכלי מאותחל בהצלחה בעזרת ה-Enums מהדף הנפרד"""
        # תוקן לפרמטר id במקום piece_id, והסרת cell מהבנאי
        piece = Piece(id="wR_1", color=PieceColor.WHITE, kind=PieceKind.ROOK)
        
        self.assertEqual(piece.id, "wR_1")
        self.assertEqual(piece.color, PieceColor.WHITE)
        self.assertEqual(piece.kind, PieceKind.ROOK)
        self.assertIsNone(piece.cell)
        self.assertEqual(piece.state, "idle")

    def test_piece_state_lifecycle(self):
        piece = Piece(id="bP_1", color=PieceColor.BLACK, kind=PieceKind.PAWN)
        piece.state = "moving"
        self.assertEqual(piece.state, "moving")
        piece.state = "captured"
        self.assertEqual(piece.state, "captured")

if __name__ == "__main__":
    unittest.main()