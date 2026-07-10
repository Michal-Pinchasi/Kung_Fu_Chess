import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.board import Board
from model.game_state import GameState, GameSnapshot, MoveResult

class TestGameStateComponents(unittest.TestCase):

    def test_game_state_initialization(self):
        """וידוא שמצב המשחק המרכזי מאותחל עם ערכי ברירת מחדל נכונים"""
        board = Board(width=8, height=8)
        state = GameState(board)
        
        self.assertEqual(state.board, board)
        self.assertFalse(state.is_game_over)
        self.assertIsNone(state.winner)

    def test_game_snapshot_creation(self):
        """וידוא שצילום המצב (Snapshot) שומר על הנתונים לקריאה-בלבד בצורה מדויקת"""
        board = Board(width=4, height=4)
        snapshot = GameSnapshot(board, is_game_over=True, winner="w")
        
        self.assertEqual(snapshot.board, board)
        self.assertTrue(snapshot.is_game_over)
        self.assertEqual(snapshot.winner, "w")

    def test_move_result_properties(self):
        """וידוא שאובייקט התשובה של המנוע שומר נכון את סטטוס הקבלה וסיבת השגיאה"""
        # מקרה של קבלה
        success_result = MoveResult(is_accepted=True, reason="ok")
        self.assertTrue(success_result.is_accepted)
        self.assertEqual(success_result.reason, "ok")
        
        # מקרה של דחייה
        fail_result = MoveResult(is_accepted=False, reason="motion_in_progress")
        self.assertFalse(fail_result.is_accepted)
        self.assertEqual(fail_result.reason, "motion_in_progress")

if __name__ == "__main__":
    unittest.main()