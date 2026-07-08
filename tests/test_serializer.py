import unittest
from serializer import TextBoardSerializer
from board import Board

class TestTextBoardSerializer(unittest.TestCase):
    def test_validate_token_valid(self):
        """בדיקת טוקנים חוקיים (נקודה וכלים)"""
        self.assertTrue(TextBoardSerializer.validate_token("."))
        self.assertTrue(TextBoardSerializer.validate_token("wK"))
        self.assertTrue(TextBoardSerializer.validate_token("bP"))

    def test_validate_token_invalid(self):
        """וידוא שטוקן לא חוקי עוצר את התוכנית"""
        with self.assertRaises(SystemExit):
            TextBoardSerializer.validate_token("xZ")
        with self.assertRaises(SystemExit):
            TextBoardSerializer.validate_token("wKK")

    def test_parse_valid_input(self):
        """בדיקת טעינת לוח מלבני תקין וחילוץ מידות"""
        input_data = "Board:\nwK . bQ\n. wN .\nCommands:\nprint board"
        board = TextBoardSerializer.parse(input_data)
        
        self.assertEqual(board.width, 3)
        self.assertEqual(board.height, 2)
        self.assertEqual(board.get_piece(0, 0), "wK")
        self.assertEqual(board.get_piece(0, 2), "bQ")

    def test_parse_row_width_mismatch(self):
        """וידוא עצירה כשהשורות לא באותו אורך"""
        input_data = "Board:\nwK .\n. bK .\nCommands:"
        with self.assertRaises(SystemExit):
            TextBoardSerializer.parse(input_data)

    def test_parse_missing_board_lines(self):
        """וידוא עצירה כשאין שורות לוח בכלל"""
        input_data = "Board:\nCommands:\nprint board"
        with self.assertRaises(SystemExit):
            TextBoardSerializer.parse(input_data)

    def test_serialize_canonical(self):
        """וידוא הדפסה בפורמט קנוני מדויק עם רווחים"""
        board = Board(width=3, height=2)
        board.set_piece(0, 0, "wK")
        board.set_piece(1, 1, "bK")
        
        expected = "wK . .\n. bK ."
        self.assertEqual(TextBoardSerializer.serialize(board), expected)

if __name__ == "__main__":
    unittest.main()