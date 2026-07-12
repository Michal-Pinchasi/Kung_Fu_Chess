import unittest
from model.board import Board
from model.game_state import GameState, GameSnapshot, MoveResult, PieceSnapshot
from model.position import Position

class TestGameStateComponents(unittest.TestCase):

    def test_game_state_initialization(self):
        board = Board(width=8, height=8)
        state = GameState(board)
        self.assertEqual(state.board, board)
        self.assertFalse(state.is_game_over)
        self.assertIsNone(state.winner)

    def test_game_snapshot_creation(self):
        """וידוא שצילום המצב שומר על הנתונים המורחבים לקריאה-בלבד בצורה מדויקת"""
        piece_snap = PieceSnapshot(id="wR_1", kind="R", color="w", x=0.0, y=0.0, state="idle")
        
        # התאמת הפרמטרים לבנאי האמיתי של GameSnapshot
        snapshot = GameSnapshot(
            board_width=8,
            board_height=8,
            pieces=[piece_snap],
            selected_cell=Position(0, 0),
            game_over=True
        )
        
        self.assertEqual(snapshot.board_width, 8)
        self.assertEqual(snapshot.board_height, 8)
        self.assertEqual(len(snapshot.pieces), 1)
        self.assertEqual(snapshot.selected_cell, Position(0, 0))
        self.assertTrue(snapshot.game_over)

    def test_move_result_properties(self):
        success_result = MoveResult(is_accepted=True, reason="ok")
        self.assertTrue(success_result.is_accepted)
        self.assertEqual(success_result.reason, "ok")
        
        fail_result = MoveResult(is_accepted=False, reason="motion_in_progress")
        self.assertFalse(fail_result.is_accepted)
        self.assertEqual(fail_result.reason, "motion_in_progress")

if __name__ == "__main__":
    unittest.main()