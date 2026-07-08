import unittest
from entities.board import Board
from engine import GameEngine
from entities.position import Position

class TestGameEngine(unittest.TestCase):
    def setUp(self):
        """הכנת סביבה נקייה לכל טסט בנפרד"""
        self.board = Board(width=3, height=3)
        self.board.set_piece(0, 0, "wK")  # מלך לבן
        self.board.set_piece(0, 1, "wP")  # רגלי לבן
        self.board.set_piece(2, 2, "bK")  # מלך שחור
        self.engine = GameEngine(self.board)

    def test_click_outside_board_ignored(self):
        """לחיצה מחוץ ללוח (פיקסלים גדולים) - מתעלמים"""
        self.engine.handle_click(500, 500)  # משבצת (5,5) לא קיימת
        self.assertIsNone(self.engine.selected_pos)

    def test_click_empty_no_selection_ignored(self):
        """לחיצה על ריק כשאין בחירה - מתעלמים"""
        self.engine.handle_click(150, 150)  # משבצת (1,1) ריקה
        self.assertIsNone(self.engine.selected_pos)

    def test_click_to_select_piece(self):
        """לחיצה ראשונה על כלי בוחרת אותו בהצלחה"""
        self.engine.handle_click(50, 50)  # משבצת (0,0) - מלך לבן
        self.assertEqual(self.engine.selected_pos.row, 0)
        self.assertEqual(self.engine.selected_pos.col, 0)

    def test_click_change_selection_friendly(self):
        """לחיצה על כלי אחר באותו צבע מחליפה את הבחירה"""
        self.engine.handle_click(50, 50)   # נבחר מלך לבן ב-(0,0)
        self.engine.handle_click(150, 50)  # לחיצה על רגלי לבן ב-(0,1)
        self.assertEqual(self.engine.selected_pos.row, 0)
        self.assertEqual(self.engine.selected_pos.col, 1)

    def test_request_move_clears_origin(self):
        """שליחת מהלך מעלימה את הכלי זמניתמשבצת המקור"""
        self.engine.handle_click(50, 50)   # נבחר מלך לבן ב-(0,0)
        self.engine.handle_click(50, 150)  # לחיצה על משבצת (1,0) ריקה
        
        # הכלי "באוויר", המקור ריק והיעד עדיין ריק
        self.assertEqual(self.board.get_piece(0, 0), ".")
        self.assertEqual(self.board.get_piece(1, 0), ".")
        self.assertEqual(len(self.engine.active_moves), 1)
        # הבחירה מתאפסת לאחר תנועה
        self.assertIsNone(self.engine.selected_pos)

    def test_request_move_same_position_ignored(self):
        """תנועה מאותה משבצת לעצמה - מתעלמים ולא מוחקים את הכלי"""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(50, 50)
        self.assertEqual(self.board.get_piece(0, 0), "wK")
        self.assertEqual(len(self.engine.active_moves), 0)

    def test_advance_time_partial_and_complete(self):
        """וידוא שהכלי נוחת ביעד רק לאחר שחלף כל הזמן הנדרש"""
        self.engine.handle_click(50, 50)
        self.engine.handle_click(50, 150)  # תנועה ל-(1,0) - לוקח 1000ms
        
        # חלף רק חלק מהזמן - הכלי עדיין לא הגיע
        self.engine.advance_time(600)
        self.assertEqual(self.board.get_piece(1, 0), ".")
        self.assertEqual(len(self.engine.active_moves), 1)
        
        # חלף שאר הזמן - הכלי הגיע והרשימה התרוקנה
        self.engine.advance_time(400)
        self.assertEqual(self.board.get_piece(1, 0), "wK")
        self.assertEqual(len(self.engine.active_moves), 0)

if __name__ == "__main__":
    unittest.main()