from model.position import Position
from model.constants import PieceKind, PieceColor
from rules.piece_rules import PieceRules

class MoveValidation:
    """אובייקט תשובה גמיש המכיל את תוצאת האימות וסיבת השגיאה במידה ונכשל[cite: 2]"""
    def __init__(self, is_valid: bool, reason: str = "ok"):
        self.is_valid = is_valid  # True/False האם המהלך מאושר לביצוע[cite: 2]
        self.reason = reason      # סיבת הסטטוס[cite: 2]

class RuleEngine:
    """מנוע החוקים הראשי של המשחק (לקריאה בלבד, אינו משנה את הלוח)[cite: 2]"""

    @staticmethod
    def validate_move(board, source: Position, destination: Position) -> MoveValidation:
        """מבצע אימות מלא למהלך מבוקש ומחזיר אובייקט MoveValidation[cite: 2]"""
        piece = board.get_piece(source.row, source.col)
        if piece == ".":
            return MoveValidation(is_valid=False, reason="empty_source")

        if not board.is_valid_position(destination.row, destination.col):
            return MoveValidation(is_valid=False, reason="outside_board")

        target = board.get_piece(destination.row, destination.col)
        if target != "." and target.color == piece.color:
            return MoveValidation(is_valid=False, reason="friendly_destination")

        legal_destinations = PieceRules.legal_destinations(board, piece, source)
        if destination not in legal_destinations:
            return MoveValidation(is_valid=False, reason="illegal_piece_move")

        return MoveValidation(is_valid=True, reason="ok")

    @staticmethod
    def get_game_winner(board) -> str:
        """
        סורק את הלוח ומחזיר מי המנצח על בסיס קיום המלכים.
        מחזיר "BLACK", "WHITE" או None במידה והמשחק נמשך[cite: 4].
        """
        white_king = False
        black_king = False
        
        for row in range(board.height):
            for col in range(board.width):
                piece = board.get_piece(row, col)
                if piece != "." and piece.kind == PieceKind.KING:
                    if piece.color == PieceColor.WHITE:
                        white_king = True
                    else:
                        black_king = True
                        
        if not white_king:
            return "BLACK"
        if not black_king:
            return "WHITE"
        return None