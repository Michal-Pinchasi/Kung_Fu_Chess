import unittest
import sys
import os

# הוספת נתיב השורש של הפרויקט
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.board import Board
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from Kung_Fu_Chess.rules.piece_rules import PieceRules

class TestPieceRules(unittest.TestCase):

    def test_rook_moves_clear_and_blocked(self):
        """1. בדיקת צריח: וידוא תנועה ב-4 כיוונים ועצירה כשנחסם על ידי כלי"""
        board = Board(width=5, height=5)
        rook = Piece("wR_1", PieceColor.WHITE, PieceKind.ROOK)
        board.add_piece(2, 2, rook) # צריח במרכז הלוח (2,2)

        # נשים כלי חוסם במשבצת (2,4) - קצה ימין של השורה
        blocker = Piece("bP_1", PieceColor.BLACK, PieceKind.PAWN)
        board.add_piece(2, 4, blocker)

        destinations = PieceRules.legal_destinations(board, rook, Position(2, 2))

        # צפויים מהלכים למעלה, למטה, שמאלה, וימינה (כולל המשבצת החוסמת, אך לא מעבר לה)
        expected_moves = {
            Position(0, 2), Position(1, 2), Position(3, 2), Position(4, 2), # טור 2
            Position(2, 0), Position(2, 1), Position(2, 3), Position(2, 4)  # שורה 2 (נעצר ב-2,4)
        }
        self.assertEqual(destinations, expected_moves)
        self.assertNotIn(Position(2, 5), destinations) # מחוץ ללוח/מעבר לחוסם

    def test_bishop_moves(self):
        """2. בדיקת רץ: וידוא תנועה חופשית באלכסונים"""
        board = Board(width=4, height=4)
        bishop = Piece("wB_1", PieceColor.WHITE, PieceKind.BISHOP)
        board.add_piece(0, 0, bishop) # רץ בפינה (0,0)

        destinations = PieceRules.legal_destinations(board, bishop, Position(0, 0))
        
        expected_moves = {Position(1, 1), Position(2, 2), Position(3, 3)}
        self.assertEqual(destinations, expected_moves)

    def test_knight_moves_near_board_edges(self):
        """3. בדיקת פרש: וידוא סינון קפיצות L שחורגות מגבולות הלוח"""
        board = Board(width=3, height=3)
        knight = Piece("wN_1", PieceColor.WHITE, PieceKind.KNIGHT)
        board.add_piece(0, 0, knight) # פרש בפינה (0,0)

        destinations = PieceRules.legal_destinations(board, knight, Position(0, 0))
        
        # מפינה (0,0) בלוח 3x3, הקפיצות החוקיות היחידות בתוך הלוח הן (1,2) ו-(2,1)
        expected_moves = {Position(1, 2), Position(2, 1)}
        self.assertEqual(destinations, expected_moves)

    def test_king_moves(self):
        """4. בדיקת מלך: וידוא תנועה של צעד אחד לכל 8 הכיוונים"""
        board = Board(width=3, height=3)
        king = Piece("wK_1", PieceColor.WHITE, PieceKind.KING)
        board.add_piece(1, 1, king) # מלך בדיוק במרכז (1,1)

        destinations = PieceRules.legal_destinations(board, king, Position(1, 1))
        self.assertEqual(len(destinations), 8) # צריך להקיף את כל 8 המשבצות מסביב

    def test_white_pawn_forward_and_diagonal_capture(self):
        """5. בדיקת רגלי לבן: צעד קדימה לריק ואכילה באלכסון כשיש אויב"""
        board = Board(width=3, height=3)
        pawn = Piece("wP_1", PieceColor.WHITE, PieceKind.PAWN)
        board.add_piece(2, 1, pawn) # רגלי לבן בשורה 2, עמודה 1

        # נשים כלי אויב באלכסון (שורה אחת מעליו, עמודה מימין)
        enemy = Piece("bK_1", PieceColor.BLACK, PieceKind.KING)
        board.add_piece(1, 2, enemy)

        destinations = PieceRules.legal_destinations(board, pawn, Position(2, 1))

        # צפוי: צעד קדימה ל-(1,1) ואכילה באלכסון ל-(1,2)
        expected_moves = {Position(1, 1), Position(1, 2)}
        self.assertEqual(destinations, expected_moves)

    def test_unknown_piece_kind_returns_empty_set(self):
        """6. בדיקת הגנה: סוג כלי לא מוכר מחזיר קבוצה ריקה"""
        board = Board(width=3, height=3)
        fake_piece = Piece("wX_1", PieceColor.WHITE, None) # סוג כלי None
        
        destinations = PieceRules.legal_destinations(board, fake_piece, Position(0, 0))
        self.assertEqual(destinations, set())

if __name__ == "__main__":
    unittest.main()