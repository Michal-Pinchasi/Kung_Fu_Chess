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
    """טסטים בסיסיים — בחירה, מהלך חוקי/לא חוקי, advance_time עם תנועה לאורך זמן."""

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

    def test_legal_move_piece_stays_at_origin_until_done(self):
        """מהלך חוקי — הכלי נשאר במקור עד שהזמן עובר (איטרציה 6)."""
        self.engine.handle_click(50, 50)   # בחירת המלך ב-(0,0)
        self.engine.handle_click(150, 50)  # יעד (0,1) — חוקי

        # מיד לאחר הלחיצה: הכלי עדיין במקור, מהלך באוויר
        self.assertEqual(self.board.get_piece(0, 0), self.white_king)
        self.assertEqual(len(self.engine.active_moves), 1)

    def test_piece_still_at_origin_after_partial_time(self):
        """אחרי 1000ms (חצי מ-2000ms) — הכלי עדיין במקור, לא הגיע ליעד."""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(150, 50)

        self.engine.advance_time(1000)

        self.assertEqual(self.board.get_piece(0, 0), self.white_king)
        self.assertEqual(self.board.get_piece(0, 1), ".")
        self.assertEqual(len(self.engine.active_moves), 1)

    def test_advance_time_completes_move_after_full_duration(self):
        """אחרי 2000ms מצטבר — הכלי מופיע ביעד ונעלם מהמקור."""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(150, 50)

        self.engine.advance_time(1000)
        self.engine.advance_time(1000)  # סה"כ 2000ms

        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(self.board.get_piece(0, 1), self.white_king)
        self.assertEqual(len(self.engine.active_moves), 0)

    def test_illegal_move_shape_ignored(self):
        """מלך מנסה לזוז שני צעדים — לא חוקי, הכל מתאפס."""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(250, 50)  # יעד (0,2) — שני צעדים, אסור
        self.assertEqual(self.board.get_piece(0, 0), self.white_king)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNone(self.engine.selected_pos)


class TestEngineCapture(unittest.TestCase):
    """טסטי אכילה ואיסור אכילה עצמית — מעודכן לתנועה לאורך זמן."""

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

        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNotNone(self.engine.selected_pos)
        self.assertEqual(self.engine.selected_pos.row, 0)
        self.assertEqual(self.engine.selected_pos.col, 2)

    def test_enemy_capture_is_blocked_by_friendly_in_path(self):
        """צריח לבן מנסה לאכול כלי שחור ב-(0,3) אך יש כלי לבן ב-(0,2) — נחסם."""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(350, 50)

        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNone(self.engine.selected_pos)

    def test_enemy_capture_clear_path_piece_stays_at_origin(self):
        """צריח לבן אוכל כלי שחור — מיד לאחר הלחיצה הכלי עדיין במקור (איטרציה 6)."""
        self.board.set_piece(0, 2, ".")
        self.engine.handle_click(50, 50)
        self.engine.handle_click(350, 50)

        # הכלי עדיין במקור, מהלך באוויר
        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(len(self.engine.active_moves), 1)

    def test_enemy_capture_completes_after_full_duration(self):
        """advance_time(2000): הצריח מגיע ליעד, כלי האויב נמחק."""
        self.board.set_piece(0, 2, ".")
        self.engine.handle_click(50, 50)
        self.engine.handle_click(350, 50)

        self.engine.advance_time(2000)

        self.assertEqual(self.board.get_piece(0, 0), ".")
        captured_square = self.board.get_piece(0, 3)
        self.assertIsInstance(captured_square, Piece)
        self.assertEqual(captured_square.color, "w")
        self.assertEqual(len(self.engine.active_moves), 0)

    def test_enemy_capture_partial_time_enemy_still_on_board(self):
        """advance_time(1000): האויב עדיין קיים ב-(0,3), הצריח עדיין ב-(0,0)."""
        self.board.set_piece(0, 2, ".")
        self.engine.handle_click(50, 50)
        self.engine.handle_click(350, 50)

        self.engine.advance_time(1000)

        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(self.board.get_piece(0, 3), self.black_pawn)
        self.assertEqual(len(self.engine.active_moves), 1)


class TestEngineBlocker(unittest.TestCase):
    """טסטי חסימות מסלול דרך ה-engine."""

    def setUp(self):
        self.board = Board(width=6, height=3)
        self.white_rook = Piece("w", "R", STRATEGIES_MAP["R"])
        self.blocker = Piece("b", "P", STRATEGIES_MAP["P"])
        self.board.set_piece(0, 0, self.white_rook)
        self.board.set_piece(0, 3, self.blocker)
        self.engine = GameEngine(self.board)

    def test_rook_blocked_by_enemy_pawn_in_engine(self):
        """צריח נחסם על ידי כלי אויב באמצע — אין active_move."""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(550, 50)

        self.assertEqual(self.board.get_piece(0, 0), self.white_rook)
        self.assertEqual(len(self.engine.active_moves), 0)
        self.assertIsNone(self.engine.selected_pos)

    def test_knight_not_blocked_in_engine(self):
        """פרש קופץ מעל חוסם — המהלך חוקי, הכלי עדיין במקור עד advance_time."""
        board = Board(width=4, height=4)
        white_knight = Piece("w", "N", STRATEGIES_MAP["N"])
        blocker = Piece("b", "P", STRATEGIES_MAP["P"])
        board.set_piece(0, 0, white_knight)
        board.set_piece(0, 1, blocker)
        engine = GameEngine(board)

        engine.handle_click(50, 50)
        engine.handle_click(150, 250)  # יעד (2,1) — קפיצת L חוקית

        # הכלי עדיין במקור (איטרציה 6), מהלך באוויר
        self.assertEqual(board.get_piece(0, 0), white_knight)
        self.assertEqual(len(engine.active_moves), 1)

        engine.advance_time(2000)
        self.assertEqual(board.get_piece(0, 0), ".")
        self.assertEqual(board.get_piece(2, 1), white_knight)


class TestEnginePawn(unittest.TestCase):
    """טסטי אינטגרציה לרגלי — מעודכן לתנועה לאורך זמן."""

    def _make_board(self):
        return Board(width=4, height=4)

    def test_white_pawn_forward_legal(self):
        """רגלי לבן זז קדימה — מיד לאחר הלחיצה הכלי עדיין במקור (איטרציה 6)."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        board.set_piece(2, 1, pawn)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(150, 150)

        self.assertEqual(board.get_piece(2, 1), pawn)  # עדיין במקור
        self.assertEqual(len(engine.active_moves), 1)

    def test_white_pawn_forward_completes_after_full_duration(self):
        """רגלי לבן מגיע ליעד רק אחרי 2000ms."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        board.set_piece(2, 1, pawn)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(150, 150)
        engine.advance_time(2000)

        self.assertEqual(board.get_piece(2, 1), ".")
        self.assertEqual(board.get_piece(1, 1), pawn)
        self.assertEqual(len(engine.active_moves), 0)

    def test_white_pawn_forward_partial_time(self):
        """אחרי 1000ms — רגלי עדיין במקור."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        board.set_piece(2, 1, pawn)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(150, 150)
        engine.advance_time(1000)

        self.assertEqual(board.get_piece(2, 1), pawn)
        self.assertEqual(board.get_piece(1, 1), ".")
        self.assertEqual(len(engine.active_moves), 1)

    def test_white_pawn_forward_blocked(self):
        """רגלי לבן מנסה לזוז לתוך משבצת תפוסה — לא חוקי."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        blocker = Piece("b", "R", STRATEGIES_MAP["R"])
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 1, blocker)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(150, 150)

        self.assertEqual(board.get_piece(2, 1), pawn)
        self.assertEqual(len(engine.active_moves), 0)
        self.assertIsNone(engine.selected_pos)

    def test_black_pawn_forward_legal(self):
        """רגלי שחור זז קדימה — הכלי עדיין במקור עד advance_time."""
        board = self._make_board()
        pawn = Piece("b", "P", STRATEGIES_MAP["P"])
        board.set_piece(1, 1, pawn)
        engine = GameEngine(board)

        engine.handle_click(150, 150)
        engine.handle_click(150, 250)

        self.assertEqual(board.get_piece(1, 1), pawn)  # עדיין במקור
        self.assertEqual(len(engine.active_moves), 1)

        engine.advance_time(2000)
        self.assertEqual(board.get_piece(1, 1), ".")
        self.assertEqual(board.get_piece(2, 1), pawn)

    def test_white_pawn_diagonal_capture(self):
        """רגלי לבן אוכל כלי אויב באלכסון — הכלי עדיין במקור עד advance_time."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        enemy = Piece("b", "K", STRATEGIES_MAP["K"])
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 2, enemy)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(250, 150)

        self.assertEqual(board.get_piece(2, 1), pawn)  # עדיין במקור
        self.assertEqual(len(engine.active_moves), 1)

    def test_white_pawn_diagonal_capture_advance_time(self):
        """advance_time(2000): הרגלי מגיע ליעד, האויב נמחק."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        enemy = Piece("b", "K", STRATEGIES_MAP["K"])
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 2, enemy)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(250, 150)
        engine.advance_time(2000)

        self.assertEqual(board.get_piece(2, 1), ".")
        result = board.get_piece(1, 2)
        self.assertIsInstance(result, Piece)
        self.assertEqual(result.color, "w")
        self.assertEqual(len(engine.active_moves), 0)

    def test_white_pawn_diagonal_empty_is_illegal(self):
        """רגלי לבן מנסה לזוז לאלכסון ריק — לא חוקי."""
        board = self._make_board()
        pawn = Piece("w", "P", STRATEGIES_MAP["P"])
        board.set_piece(2, 1, pawn)
        engine = GameEngine(board)

        engine.handle_click(150, 250)
        engine.handle_click(250, 150)

        self.assertEqual(board.get_piece(2, 1), pawn)
        self.assertEqual(len(engine.active_moves), 0)
        self.assertIsNone(engine.selected_pos)


if __name__ == "__main__":
    unittest.main()
