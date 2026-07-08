import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from entities.board import Board
from entities.piece import Piece
from entities.position import Position
from entities.strategies import STRATEGIES_MAP
from engine import GameEngine


class TestGameEngineBasic(unittest.TestCase):
    """טסטים בסיסיים מאיטרציות קודמות — בחירה, מהלך חוקי/לא חוקי, advance_time."""

    def setUp(self):
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
        self.engine.handle_click(50, 50)  # משבצת (0,0)
        self.assertEqual(self.engine.selected_pos.row, 0)
        self.assertEqual(self.engine.selected_pos.col, 0)

    def test_legal_move_sends_piece_to_air(self):
        """מלך זז צעד אחד — הכלי עוזב את המקור ונכנס לאוויר."""
        self.engine.handle_click(50, 50)   # בחירת המלך ב-(0,0)
        self.engine.handle_click(150, 50)  # יעד (0,1) — חוקי
        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(len(self.engine.active_moves), 1)

    def test_illegal_move_shape_ignored(self):
        """מלך מנסה לזוז שני צעדים — לא חוקי, הכל מתאפס."""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(250, 50)  # יעד (0,2) — שני צעדים, אסור
        self.assertEqual(self.board.get_piece(0, 0), self.white_king)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNone(self.engine.selected_pos)

    def test_advance_time_completes_move(self):
        self.engine.handle_click(50, 50)
        self.engine.handle_click(150, 50)
        self.engine.advance_time(1000)
        self.assertEqual(self.board.get_piece(0, 1), self.white_king)
        self.assertEqual(len(self.engine.active_moves), 0)


class TestEngineCapture(unittest.TestCase):
    """טסטי אכילה ואיסור אכילה עצמית — איטרציה 4."""

    def setUp(self):
        # לוח 4x4: צריח לבן ב-(0,0), כלי שחור ב-(0,3), כלי לבן נוסף ב-(0,2)
        self.board = Board(width=4, height=4)
        self.white_rook = Piece("w", "R", STRATEGIES_MAP["R"])
        self.black_pawn = Piece("b", "P", STRATEGIES_MAP["P"])
        self.white_pawn = Piece("w", "P", STRATEGIES_MAP["P"])

        self.board.set_piece(0, 0, self.white_rook)
        self.board.set_piece(0, 3, self.black_pawn)
        self.board.set_piece(0, 2, self.white_pawn)

        self.engine = GameEngine(self.board)

    def test_friendly_capture_is_illegal_and_reselects(self):
        """לחיצה על כלי ידידותי ביעד — הבחירה עוברת לכלי הידידותי, אין מהלך."""
        self.engine.handle_click(50, 50)   # בוחר צריח לבן ב-(0,0)
        self.engine.handle_click(250, 50)  # לחיצה על כלי לבן ב-(0,2)

        # אין מהלך באוויר — הצריח נשאר במקומו
        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(len(self.engine.active_moves), 0)
        # הבחירה עברה לכלי הלבן ב-(0,2)
        self.assertIsNotNone(self.engine.selected_pos)
        self.assertEqual(self.engine.selected_pos.row, 0)
        self.assertEqual(self.engine.selected_pos.col, 2)

    def test_enemy_capture_is_blocked_by_friendly_in_path(self):
        """צריח לבן מנסה לאכול כלי שחור ב-(0,3) אך יש כלי לבן ב-(0,2) — נחסם."""
        self.engine.handle_click(50, 50)   # בוחר צריח לבן ב-(0,0)
        self.engine.handle_click(350, 50)  # יעד (0,3) — שחור, אבל נחסם ב-(0,2)

        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNone(self.engine.selected_pos)

    def test_enemy_capture_clear_path_is_legal(self):
        """צריח לבן אוכל כלי שחור — מסלול פנוי, המהלך נשלח לאוויר."""
        # הסרת החוסם הלבן מ-(0,2) לצורך הטסט
        self.board.set_piece(0, 2, ".")
        self.engine.handle_click(50, 50)   # בוחר צריח לבן ב-(0,0)
        self.engine.handle_click(350, 50)  # יעד (0,3) — כלי שחור, מסלול פנוי

        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(len(self.engine.active_moves), 1)

    def test_advance_time_removes_captured_enemy(self):
        """advance_time: הכלי האוכל מגיע ליעד, הכלי האויב נמחק."""
        self.board.set_piece(0, 2, ".")  # מסלול פנוי

        self.engine.handle_click(50, 50)
        self.engine.handle_click(350, 50)  # צריח לבן → (0,3) שבו כלי שחור

        self.engine.advance_time(1000)

        # הצריח הלבן עכשיו ב-(0,3), הכלי השחור נמחק
        captured_square = self.board.get_piece(0, 3)
        self.assertIsInstance(captured_square, Piece)
        self.assertEqual(captured_square.color, "w")
        self.assertEqual(len(self.engine.active_moves), 0)


class TestEngineBlocker(unittest.TestCase):
    """טסטי חסימות מסלול דרך ה-engine — איטרציה 4."""

    def setUp(self):
        # לוח 6x3: צריח לבן ב-(0,0), רגלי שחור חוסם ב-(0,3), יעד ב-(0,5)
        self.board = Board(width=6, height=3)
        self.white_rook = Piece("w", "R", STRATEGIES_MAP["R"])
        self.blocker = Piece("b", "P", STRATEGIES_MAP["P"])
        self.board.set_piece(0, 0, self.white_rook)
        self.board.set_piece(0, 3, self.blocker)
        self.engine = GameEngine(self.board)

    def test_rook_blocked_by_enemy_pawn_in_engine(self):
        """דרך ה-engine: צריח נחסם על ידי כלי אויב באמצע — אין active_move."""
        self.engine.handle_click(50, 50)   # בוחר צריח ב-(0,0)
        self.engine.handle_click(550, 50)  # יעד (0,5) — חוסם ב-(0,3)

        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNone(self.engine.selected_pos)

    def test_knight_not_blocked_in_engine(self):
        """דרך ה-engine: פרש קופץ מעל חוסם — המהלך חוקי."""
        board = Board(width=4, height=4)
        white_knight = Piece("w", "N", STRATEGIES_MAP["N"])
        blocker = Piece("b", "P", STRATEGIES_MAP["P"])
        board.set_piece(0, 0, white_knight)
        board.set_piece(0, 1, blocker)  # חוסם בשורה — לא רלוונטי לפרש
        engine = GameEngine(board)

        engine.handle_click(50, 50)   # בוחר פרש ב-(0,0)
        engine.handle_click(150, 250) # יעד (2,1) — קפיצת L חוקית

        self.assertEqual(board.get_piece(0, 0), ".")
        self.assertEqual(len(engine.active_moves), 1)


class TestEnginePawn(unittest.TestCase):
    """טסטי אינטגרציה לרגלי דרך ה-engine — איטרציה 5."""

    def _make_board(self):
        return Board(width=4, height=4)

    # --- תנועה קדימה ---

    def test_white_pawn_forward_legal(self):
        """רגלי לבן זז שורה אחת קדימה לתוך ריק — active_move נוצר."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        board.set_piece(2, 1, pawn)
        engine = GameEngine(board)

        engine.handle_click(150, 250)  # בחירת רגלי ב-(2,1)
        engine.handle_click(150, 150)  # יעד (1,1) — ריק, חוקי

        self.assertEqual(board.get_piece(2, 1), ".")
        self.assertEqual(len(engine.active_moves), 1)

    def test_white_pawn_forward_blocked(self):
        """רגלי לבן מנסה לזוז לתוך משבצת תפוסה קדימה — לא חוקי."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        blocker = Piece("b", "R", STRATEGIES_MAP["R"])
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 1, blocker)  # חוסם ישירות מול
        engine = GameEngine(board)

        engine.handle_click(150, 250)  # בחירת רגלי ב-(2,1)
        engine.handle_click(150, 150)  # יעד (1,1) — תפוס, לא חוקי

        self.assertEqual(board.get_piece(2, 1), pawn)
        self.assertEqual(len(engine.active_moves), 0)
        self.assertIsNone(engine.selected_pos)

    def test_black_pawn_forward_legal(self):
        """רגלי שחור זז שורה אחת קדימה (למטה) — active_move נוצר."""
        board = self._make_board()
        pawn = Piece("b", "P", STRATEGIES_MAP["P"])
        board.set_piece(1, 1, pawn)
        engine = GameEngine(board)

        engine.handle_click(150, 150)  # בחירת רגלי ב-(1,1)
        engine.handle_click(150, 250)  # יעד (2,1) — ריק, חוקי

        self.assertEqual(board.get_piece(1, 1), ".")
        self.assertEqual(len(engine.active_moves), 1)

    # --- אכילה באלכסון ---

    def test_white_pawn_diagonal_capture(self):
        """רגלי לבן אוכל כלי אויב באלכסון — active_move נוצר."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        enemy = Piece("b", "K", STRATEGIES_MAP["K"])
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 2, enemy)
        engine = GameEngine(board)

        engine.handle_click(150, 250)  # בחירת רגלי ב-(2,1)
        engine.handle_click(250, 150)  # יעד (1,2) — אויב, חוקי

        self.assertEqual(board.get_piece(2, 1), ".")
        self.assertEqual(len(engine.active_moves), 1)

    def test_white_pawn_diagonal_capture_advance_time(self):
        """advance_time: הרגלי מגיע ליעד, האויב נמחק."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        enemy = Piece("b", "K", STRATEGIES_MAP["K"])
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 2, enemy)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(250, 150)
        engine.advance_time(1000)

        result = board.get_piece(1, 2)
        self.assertIsInstance(result, Piece)
        self.assertEqual(result.color, "w")
        self.assertEqual(len(engine.active_moves), 0)

    def test_white_pawn_diagonal_empty_is_illegal(self):
        """רגלי לבן מנסה לזוז לאלכסון ריק — לא חוקי."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        board.set_piece(2, 1, pawn)
        # (1,2) ריק
        engine = GameEngine(board)

        engine.handle_click(150, 250)  # בחירת רגלי ב-(2,1)
        engine.handle_click(250, 150)  # יעד (1,2) — ריק, לא חוקי

        self.assertEqual(board.get_piece(2, 1), pawn)
        self.assertEqual(len(engine.active_moves), 0)
        self.assertIsNone(engine.selected_pos)


if __name__ == "__main__":
    unittest.main()
