import unittest
import sys
import os

# הוספת נתיב השורש כדי שפייתון ימצא את תיקיית entities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from serializer import TextBoardSerializer
from entities.board import Board
from entities.piece import Piece

class TestTextBoardSerializer(unittest.TestCase):
    def test_validate_token_valid(self):
        self.assertTrue(TextBoardSerializer.validate_token("."))
        self.assertTrue(TextBoardSerializer.validate_token("wK"))
        self.assertTrue(TextBoardSerializer.validate_token("bP"))

    def test_validate_token_invalid(self):
        with self.assertRaises(SystemExit):
            TextBoardSerializer.validate_token("xZ")

    def test_parse_valid_input(self):
        input_data = "Board:\nwK . bQ\nCommands:\nprint board"
        board = TextBoardSerializer.parse(input_data)
        
        self.assertEqual(board.width, 3)
        self.assertEqual(board.height, 1)
        
        # וידוא ש-get_piece מחזיר אובייקט Piece אמיתי ומאמת את מאפייניו
        piece_1 = board.get_piece(0, 0)
        self.assertIsInstance(piece_1, Piece)
        self.assertEqual(piece_1.color, "w")
        self.assertEqual(piece_1.role, "K")

    def test_parse_row_width_mismatch(self):
        input_data = "Board:\nwK .\n. bK .\nCommands:"
        with self.assertRaises(SystemExit):
            TextBoardSerializer.parse(input_data)

    def test_serialize_canonical(self):
        # טעינת לוח ובדיקה שההדפסה שלו חוזרת במדויק כמחרוזת קנונית
        input_data = "Board:\nwK . bQ\nCommands:\nprint board"
        board = TextBoardSerializer.parse(input_data)
        expected = "wK . bQ"
        self.assertEqual(TextBoardSerializer.serialize(board), expected)

if __name__ == "__main__":
    unittest.main()