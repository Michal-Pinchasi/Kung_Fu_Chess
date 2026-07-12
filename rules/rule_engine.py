from model.position import Position
from Kung_Fu_Chess.rules.piece_rules import PieceRules

class MoveValidation:
    """אובייקט תשובה גמיש המכיל את תוצאת האימות וסיבת השגיאה במידה ונכשל"""
    def __init__(self, is_valid: bool, reason: str = "ok"):
        self.is_valid = is_valid  # True/False האם המהלך מאושר לביצוע
        self.reason = reason      # סיבת הסטטוס: "ok", "empty_source", "friendly_destination", "illegal_piece_move"


class RuleEngine:
    """מנוע החוקים הראשי של המשחק (לקריאה בלבד, אינו משנה את הלוח)"""

    @staticmethod
    def validate_move(board, source: Position, destination: Position) -> MoveValidation:
        """
        מבצע אימות מלא למהלך מבוקש ומחזיר אובייקט MoveValidation.
        פונקציה זו אינה משנה את מצב הלוח.
        """
        # 1. בדיקה שיש בכלל כלי במשבצת המקור
        piece = board.get_piece(source.row, source.col)
        if piece == ".":
            return MoveValidation(is_valid=False, reason="empty_source")

        # 2. בדיקה האם היעד נמצא בתוך גבולות הלוח
        if not board.is_valid_position(destination.row, destination.col):
            return MoveValidation(is_valid=False, reason="outside_board")

        # 3. בדיקה האם היעד מכיל כלי ידידותי (חסימת אכילה עצמית)
        target = board.get_piece(destination.row, destination.col)
        if target != "." and target.color == piece.color:
            return MoveValidation(is_valid=False, reason="friendly_destination")

        # 4. בדיקה האם המהלך חוקי לפי החוקים הגיאומטריים של סוג הכלי הספציפי
        legal_destinations = PieceRules.legal_destinations(board, piece, source)
        if destination not in legal_destinations:
            return MoveValidation(is_valid=False, reason="illegal_piece_move")

        # אם המהלך עבר את כל סינוני שומרי הסף - הוא חוקי ומאושר!
        return MoveValidation(is_valid=True, reason="ok")