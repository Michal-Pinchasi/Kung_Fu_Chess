import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.board import Board
from model.piece import Piece
from model.position import Position
from model.strategies import (
    king_move_strategy, rook_move_strategy, bishop_strategy,
    queen_strategy, knight_strategy, pawn_strategy, STRATEGIES_MAP
)


def make_board_with_blocker(rows, cols, blocker_row, blocker_col, blocker_color="w"):
    """פונקציית עזר: יוצרת לוח ומציבה כלי רגלי חוסם במשבצת נתונה."""
    board = Board(width=cols, height=rows)
    blocker = Piece(blocker_color, "P", STRATEGIES_MAP["P"])
    board.set_piece(blocker_row, blocker_col, blocker)
    return board


class TestKingStrategy(unittest.TestCase):
    def setUp(self):
        self.center = Position(2, 2)

    def test_one_step_horizontal(self):
        self.assertTrue(king_move_strategy(self.center, Position(2, 3)))

    def test_one_step_diagonal(self):
        self.assertTrue(king_move_strategy(self.center, Position(3, 3)))

    def test_two_steps_illegal(self):
        self.assertFalse(king_move_strategy(self.center, Position(2, 4)))


class TestRookStrategy(unittest.TestCase):
    def setUp(self):
        self.origin = Position(2, 0)

    def test_horizontal_clear_path(self):
        board = Board(width=6, height=5)
        self.assertTrue(rook_move_strategy(self.origin, Position(2, 5), board))

    def test_vertical_clear_path(self):
        board = Board(width=6, height=5)
        self.assertTrue(rook_move_strategy(self.origin, Position(0, 0), board))

    def test_diagonal_illegal(self):
        board = Board(width=6, height=5)
        self.assertFalse(rook_move_strategy(self.origin, Position(3, 3), board))

    def test_blocked_by_friendly_pawn(self):
        """צריח נחסם על ידי כלי ידידותי (לבן) באמצע המסלול."""
        board = make_board_with_blocker(5, 6, blocker_row=2, blocker_col=3, blocker_color="w")
        # צריח לבן מנסה לנוע מ-(2,0) ל-(2,5) — חוסם לבן ב-(2,3)
        self.assertFalse(rook_move_strategy(self.origin, Position(2, 5), board))

    def test_blocked_by_enemy_pawn(self):
        """צריח נחסם על ידי כלי אויב (שחור) באמצע המסלול."""
        board = make_board_with_blocker(5, 6, blocker_row=2, blocker_col=3, blocker_color="b")
        self.assertFalse(rook_move_strategy(self.origin, Position(2, 5), board))

    def test_not_blocked_when_path_clear(self):
        """כשאין חוסם — הצריח עובר."""
        board = Board(width=6, height=5)
        self.assertTrue(rook_move_strategy(self.origin, Position(2, 4), board))

    def test_capture_adjacent_square_always_clear(self):
        """אכילה של משבצת צמודה — אין ביניים, תמיד חוקי מבחינת מסלול."""
        board = Board(width=6, height=5)
        self.assertTrue(rook_move_strategy(self.origin, Position(2, 1), board))


class TestBishopStrategy(unittest.TestCase):
    def setUp(self):
        self.origin = Position(0, 0)

    def test_diagonal_clear_path(self):
        board = Board(width=5, height=5)
        self.assertTrue(bishop_strategy(self.origin, Position(4, 4), board))

    def test_straight_illegal(self):
        board = Board(width=5, height=5)
        self.assertFalse(bishop_strategy(self.origin, Position(0, 3), board))

    def test_blocked_by_friendly_pawn_on_diagonal(self):
        """רץ נחסם על ידי כלי ידידותי באמצע האלכסון."""
        board = make_board_with_blocker(5, 5, blocker_row=2, blocker_col=2, blocker_color="w")
        # רץ מ-(0,0) ל-(4,4) — חוסם ב-(2,2)
        self.assertFalse(bishop_strategy(self.origin, Position(4, 4), board))

    def test_blocked_by_enemy_pawn_on_diagonal(self):
        """רץ נחסם על ידי כלי אויב באמצע האלכסון."""
        board = make_board_with_blocker(5, 5, blocker_row=2, blocker_col=2, blocker_color="b")
        self.assertFalse(bishop_strategy(self.origin, Position(4, 4), board))

    def test_one_step_diagonal_never_blocked(self):
        """צעד אחד אלכסוני — אין משבצות ביניים, תמיד חוקי מבחינת מסלול."""
        board = Board(width=5, height=5)
        self.assertTrue(bishop_strategy(self.origin, Position(1, 1), board))


class TestQueenStrategy(unittest.TestCase):
    def setUp(self):
        self.origin = Position(2, 2)

    def test_horizontal_clear(self):
        board = Board(width=6, height=5)
        self.assertTrue(queen_strategy(self.origin, Position(2, 5), board))

    def test_diagonal_clear(self):
        board = Board(width=6, height=5)
        self.assertTrue(queen_strategy(self.origin, Position(4, 4), board))

    def test_knight_shape_illegal(self):
        board = Board(width=6, height=5)
        self.assertFalse(queen_strategy(self.origin, Position(4, 3), board))

    def test_blocked_on_rank(self):
        """מלכה נחסמת על ידי חוסם בטור."""
        board = make_board_with_blocker(5, 6, blocker_row=2, blocker_col=4, blocker_color="b")
        self.assertFalse(queen_strategy(self.origin, Position(2, 5), board))


class TestKnightStrategy(unittest.TestCase):
    def setUp(self):
        self.center = Position(2, 2)

    def test_valid_L_shape(self):
        self.assertTrue(knight_strategy(self.center, Position(4, 3)))
        self.assertTrue(knight_strategy(self.center, Position(3, 4)))

    def test_invalid_straight(self):
        self.assertFalse(knight_strategy(self.center, Position(2, 4)))

    def test_knight_jumps_over_blocker(self):
        """פרש מדלג מעל חוסם — board עם כלי בנתיב לא חוסם אותו."""
        board = make_board_with_blocker(5, 5, blocker_row=2, blocker_col=3, blocker_color="w")
        # הפרש ב-(2,2) קופץ ל-(4,3) — חוסם ב-(2,3) לא רלוונטי
        self.assertTrue(knight_strategy(self.center, Position(4, 3), board))

    def test_knight_jumps_over_multiple_blockers(self):
        """פרש קופץ גם כשיש כמה כלים בסביבתו."""
        board = Board(width=5, height=5)
        for r, c in [(2, 3), (3, 2), (3, 3)]:
            board.set_piece(r, c, Piece("b", "P", STRATEGIES_MAP["P"]))
        self.assertTrue(knight_strategy(self.center, Position(4, 3), board))


class TestPawnStrategy(unittest.TestCase):
    """טסטים מלאים לחוקי תנועה ואכילה של הרגלי — איטרציה 5."""

    def _make_pawn(self, color):
        return Piece(color, "P", STRATEGIES_MAP["P"])

    def _make_enemy(self, color):
        """מחזיר כלי של הצבע הנגדי."""
        enemy_color = "b" if color == "w" else "w"
        return Piece(enemy_color, "K", STRATEGIES_MAP["K"])

    # --- תנועה קדימה חוקית ---

    def test_white_pawn_moves_forward_to_empty(self):
        """רגלי לבן זז שורה אחת למעלה לתוך משבצת ריקה."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("w")
        board.set_piece(2, 1, pawn)
        self.assertTrue(pawn_strategy(Position(2, 1), Position(1, 1), board, piece=pawn))

    def test_black_pawn_moves_forward_to_empty(self):
        """רגלי שחור זז שורה אחת למטה לתוך משבצת ריקה."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("b")
        board.set_piece(1, 1, pawn)
        self.assertTrue(pawn_strategy(Position(1, 1), Position(2, 1), board, piece=pawn))

    # --- חסימה קדימה ---

    def test_white_pawn_blocked_by_friendly_ahead(self):
        """תנועה קדימה נחסמת כשיש כלי ידידותי ישירות מול הרגלי."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("w")
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 1, Piece("w", "K", STRATEGIES_MAP["K"]))
        self.assertFalse(pawn_strategy(Position(2, 1), Position(1, 1), board, piece=pawn))

    def test_white_pawn_blocked_by_enemy_ahead(self):
        """תנועה קדימה נחסמת גם כשיש כלי אויב ישירות מול הרגלי (אי-אפשר לאכול ישר)."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("w")
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 1, Piece("b", "R", STRATEGIES_MAP["R"]))
        self.assertFalse(pawn_strategy(Position(2, 1), Position(1, 1), board, piece=pawn))

    # --- איסור תנועה כפולה ---

    def test_white_pawn_cannot_move_two_squares(self):
        """רגלי לבן לא יכול לזוז שתי משבצות קדימה."""
        board = Board(width=4, height=5)
        pawn = self._make_pawn("w")
        board.set_piece(3, 1, pawn)
        self.assertFalse(pawn_strategy(Position(3, 1), Position(1, 1), board, piece=pawn))

    def test_black_pawn_cannot_move_two_squares(self):
        """רגלי שחור לא יכול לזוז שתי משבצות קדימה."""
        board = Board(width=4, height=5)
        pawn = self._make_pawn("b")
        board.set_piece(1, 1, pawn)
        self.assertFalse(pawn_strategy(Position(1, 1), Position(3, 1), board, piece=pawn))

    # --- איסור תנועה לאחור ---

    def test_white_pawn_cannot_move_backward(self):
        """רגלי לבן לא יכול לזוז אחורה (שורה גדלה)."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("w")
        board.set_piece(1, 1, pawn)
        self.assertFalse(pawn_strategy(Position(1, 1), Position(2, 1), board, piece=pawn))

    # --- אכילה באלכסון ---

    def test_white_pawn_captures_diagonally(self):
        """רגלי לבן אוכל כלי אויב באלכסון קדימה."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("w")
        enemy = self._make_enemy("w")
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 2, enemy)
        self.assertTrue(pawn_strategy(Position(2, 1), Position(1, 2), board, piece=pawn))

    def test_black_pawn_captures_diagonally(self):
        """רגלי שחור אוכל כלי אויב באלכסון קדימה."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("b")
        enemy = self._make_enemy("b")
        board.set_piece(1, 1, pawn)
        board.set_piece(2, 2, enemy)
        self.assertTrue(pawn_strategy(Position(1, 1), Position(2, 2), board, piece=pawn))

    def test_pawn_cannot_capture_empty_diagonal(self):
        """אלכסון ריק — אסור לרגלי לזוז לשם."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("w")
        board.set_piece(2, 1, pawn)
        # (1,2) ריק
        self.assertFalse(pawn_strategy(Position(2, 1), Position(1, 2), board, piece=pawn))

    def test_pawn_cannot_capture_friendly_diagonal(self):
        """אלכסון עם כלי ידידותי — אסור לרגלי לזוז לשם."""
        board = Board(width=4, height=4)
        pawn = self._make_pawn("w")
        friendly = Piece("w", "K", STRATEGIES_MAP["K"])
        board.set_piece(2, 1, pawn)
        board.set_piece(1, 2, friendly)
        self.assertFalse(pawn_strategy(Position(2, 1), Position(1, 2), board, piece=pawn))

    # --- תאימות וסיווג ---

    def test_pawn_in_strategies_map(self):
        self.assertIn("P", STRATEGIES_MAP)
        self.assertEqual(STRATEGIES_MAP["P"], pawn_strategy)

    def test_pawn_returns_false_without_board_or_piece(self):
        """ללא board וללא piece — מחזיר False בלי קריסה."""
        self.assertFalse(pawn_strategy(Position(2, 1), Position(1, 1)))


if __name__ == "__main__":
    unittest.main()
