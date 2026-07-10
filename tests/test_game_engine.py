import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.board import Board
from model.game_state import GameState
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from engine.game_engine import GameEngine

class TestGameEngineFull(unittest.TestCase):

    def setUp(self):
        """הכנת לוח משחק, מצב ומנוע ייעודיים לכל טסט בנפרד"""
        self.board = Board(width=4, height=4)
        self.state = GameState(self.board)
        self.engine = GameEngine(self.state)
        
        # הוספת צריח לבן ב-(0,0) ומלך שחור ב-(0,3) לטובת תרחישי הבדיקה
        self.white_rook = Piece("wR_1", PieceColor.WHITE, PieceKind.ROOK)
        self.black_king = Piece("bK_1", PieceColor.BLACK, PieceKind.KING)
        
        self.board.add_piece(0, 0, self.white_rook)
        self.board.add_piece(0, 3, self.black_king)

    def test_request_move_success(self):
        """1. וידוא שמהלך חוקי מתקבל בהצלחה ומייצר תנועה פעילה בבורר (עדיין לא על הלוח)"""
        source = Position(0, 0)
        destination = Position(0, 2) # מהלך ישר חוקי לצריח
        
        result = self.engine.request_move(source, destination)
        
        # בדיקת אובייקט ה-MoveResult
        self.assertTrue(result.is_accepted)
        self.assertEqual(result.reason, "ok")
        
        # וידוא שהכלי עבר למצב בתנועה (moving)
        self.assertEqual(self.white_rook.state, "moving")
        
        # וידוא שהכלי עדיין פיזית במקור על הלוח (כי התנועה באוויר לוקחת זמן!)
        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)

    def test_request_move_rejected_when_game_over(self):
        """2. וידוא שמהלך נחסם מיידית אם המשחק מוגדר כהסתיים"""
        self.state.is_game_over = True
        
        result = self.engine.request_move(Position(0, 0), Position(0, 2))
        
        self.assertFalse(result.is_accepted)
        self.assertEqual(result.reason, "game_over")

    def test_request_move_rejected_when_motion_in_progress(self):
        """3. וידוא שמהלך נחסם אם יש כבר תנועה פעילה על אותו מסלול/כלי בבורר"""
        source = Position(0, 0)
        destination = Position(0, 2)
        
        # שליחת מהלך ראשון בהצלחה (הצריח כעת באוויר)
        self.engine.request_move(source, destination)
        
        # ניסיון לשלוח מהלך נוסף עם אותו צריח בעודו באוויר
        second_result = self.engine.request_move(source, Position(0, 1))
        
        self.assertFalse(second_result.is_accepted)
        self.assertEqual(second_result.reason, "motion_in_progress")

    def test_request_move_rejected_by_rule_engine(self):
        """4. וידוא שמהלך נדחה ומעתיק את הסיבה הנכונה אם הוא נכשל במנוע החוקים (למשל מהלך לא חוקי)"""
        source = Position(0, 0)
        destination = Position(1, 1) # צריח מנסה לזוז באלכסון
        
        result = self.engine.request_move(source, destination)
        
        self.assertFalse(result.is_accepted)
        self.assertEqual(result.reason, "illegal_piece_move") # הסיבה הועתקה מהשופט

    def test_wait_advances_time_and_completes_move(self):
        """5. וידוא שפונקציית wait מקדמת זמן, משלימה את התנועה ומעדכנת את הלוח פיזית"""
        # התחלת מהלך חוקי
        self.engine.request_move(Position(0, 0), Position(0, 2))
        
        # קריאה ל-wait שתקדם זמן מדומה ב-1000 מילישניות (מספיק כדי לסיים את התנועה)
        self.engine.wait(1000)
        
        # וידוא שהכלי הגיע פיזית ליעד ומשבצת המקור התרוקנה
        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(self.board.get_piece(0, 2), self.white_rook)
        self.assertEqual(self.white_rook.state, "idle") # חזר למנוחה

    def test_wait_triggers_king_capture_and_ends_game(self):
        """6. וידוא שקידום זמן שמסתיים באכילת מלך מקפיץ התראה ומסיים את המשחק"""
        # צריח לבן ב-(0,0) מבקש מהלך אכילה ישיר אל המלך השחור ב-(0,3)
        self.engine.request_move(Position(0, 0), Position(0, 3))
        
        # קידום זמן לסיום המהלך
        self.engine.wait(1000)
        
        # וידוא שאכילת המלך זוהתה והדגל של סיום המשחק עודכן ל-True במצב המשחק
        self.assertTrue(self.state.is_game_over)

    def test_get_snapshot(self):
        """7. וידוא שייצור ה-Snapshot מחזיר אובייקט נתונים מדויק ותואם למצב הנוכחי"""
        snapshot = self.engine.get_snapshot()
        
        self.assertIsInstance(snapshot, GameSnapshot)
        self.assertEqual(snapshot.board, self.board)
        self.assertEqual(snapshot.is_game_over, self.state.is_game_over)

if __name__ == "__main__":
    unittest.main()