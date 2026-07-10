import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind

class TestBoard(unittest.TestCase):
    def test_board_initialization(self):
        """1. אחסון רוחב וגובה: וידוא שהלוח מאותחל עם הממדים הנכונים וכולו ריק בהתחלה"""
        board = Board(width=4, height=3)
        self.assertEqual(board.width, 4)
        self.assertEqual(board.height, 3)
        for r in range(3):
            for c in range(4):
                self.assertEqual(board.get_piece(r, c), ".")

    def test_is_valid_position(self):
        """2. בדיקה האם תא נמצא בגבולות: וידוא זיהוי נכון של גבולות הלוח"""
        board = Board(width=3, height=2)
        self.assertTrue(board.is_valid_position(0, 0))
        self.assertTrue(board.is_valid_position(1, 2))
        self.assertFalse(board.is_valid_position(-1, 0))
        self.assertFalse(board.is_valid_position(2, 0))
        self.assertFalse(board.is_valid_position(0, 3))

    def test_add_piece_success_and_query(self):
        """3. הוספת כלי ושאילתת כלי בתא: וידוא הצבה וקריאה מוצלחת של כלי"""
        board = Board(width=3, height=3)
        piece = Piece(piece_id="wK_1", color=PieceColor.WHITE, kind=PieceKind.KING)
        
        success = board.add_piece(1, 2, piece)
        self.assertTrue(success)
        self.assertEqual(board.get_piece(1, 2), piece)

    def test_add_piece_duplicate_occupancy_rejected(self):
        """4. דחיית תפוסה כפולה: וידוא שלא ניתן להוסיף שני כלים לאותה משבצת"""
        board = Board(width=3, height=3)
        piece1 = Piece(piece_id="wK_1", color=PieceColor.WHITE, kind=PieceKind.KING)
        piece2 = Piece(piece_id="bR_1", color=PieceColor.BLACK, kind=PieceKind.ROOK)
        
        # הוספת כלי ראשון מצליחה
        self.assertTrue(board.add_piece(1, 1, piece1))
        
        # ניסיון להוסיף כלי שני לאותה משבצת נכשל ומחזיר False
        self.assertFalse(board.add_piece(1, 1, piece2))
        # המשבצת נשארת של הכלי הראשון
        self.assertEqual(board.get_piece(1, 1), piece1)

    def test_remove_piece(self):
        """5. הסרת כלי: וידוא שהסרה מנקה את המשבצת ומחזירה אותה ל-`.`"""
        board = Board(width=3, height=3)
        piece = Piece(piece_id="wP_1", color=PieceColor.WHITE, kind=PieceKind.PAWN)
        
        board.add_piece(0, 0, piece)
        self.assertEqual(board.get_piece(0, 0), piece)
        
        board.remove_piece(0, 0)
        self.assertEqual(board.get_piece(0, 0), ".")

    def test_move_piece(self):
        """6. הזזת כלי לאחר שמהלך אומת: וידוא העברה חלקה ומעדכנת מקור ויעד"""
        board = Board(width=3, height=3)
        piece = Piece(piece_id="wR_1", color=PieceColor.WHITE, kind=PieceKind.ROOK)
        board.add_piece(0, 0, piece)
        
        source = Position(0, 0)
        destination = Position(0, 2)
        
        # ביצוע ההזזה
        board.move_piece(source, destination)
        
        # המקור צריך להתנקות, והיעד צריך להתעדכן בכלי
        self.assertEqual(board.get_piece(0, 0), ".")
        self.assertEqual(board.get_piece(0, 2), piece)
        self.assertEqual(piece.cell, destination)

if __name__ == "__main__":
    unittest.main()