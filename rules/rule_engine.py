from model.position import Position
from model.constants import PieceKind, PieceColor
from rules.piece_rules import PieceRules

class ValidationResult:
    def __init__(self, is_valid: bool, reason: str = "ok"):
        self.is_valid = is_valid
        self.reason = reason

class RuleEngine:
    @staticmethod
    def validate_move(board, source: Position, destination: Position) -> ValidationResult:
        """
        מבצע בדיקה סטטית וחוקתית מלאה על ניסיון תנועה בלוח.
        מנוע החוקים לא משנה מצב או מזיז כלים, אלא רק מחזיר אישור או סירוב.
        """
        # 1. בדיקה שמשבצת המקור נמצאת בגבולות הלוח
        if not board.is_valid_position(source.row, source.col):
            return ValidationResult(False, "outside_board")

        piece = board.get_piece(source.row, source.col)
        
        # 2. בדיקה שיש כלי במשבצת המקור
        if piece == ".":
            return ValidationResult(False, "empty_source")
            
        # 3. בדיקה שמשבצת היעד נמצאת בגבולות הלוח
        if not board.is_valid_position(destination.row, destination.col):
            return ValidationResult(False, "outside_board")
            
        target_piece = board.get_piece(destination.row, destination.col)
        
        # 4. בדיקה שאין כלי ידידותי במשבצת היעד
        if target_piece != "." and target_piece.color == piece.color:
            return ValidationResult(False, "friendly_destination")
            
        # 5. בדיקה גיאומטרית מול חוקי התנועה הספציפיים של סוג הכלי
        legal_destinations = PieceRules.legal_destinations(board, piece, source)
        if destination not in legal_destinations:
            return ValidationResult(False, "illegal_piece_move")
            
        return ValidationResult(True, "ok")

    @staticmethod
    def get_game_winner(board) -> str or None:
        """
        סורק את הלוח ומזהה האם אחד המלכים חסר (חוסל).
        אם המלך השחור חסר -> הלבן מנצח ("WHITE").
        אם המלך הלבן חסר -> השחור מנצח ("BLACK").
        """
        white_king_exists = False
        black_king_exists = False

        # סריקה יסודית של כל משבצות הלוח
        for row in range(board.height):
            for col in range(board.width):
                piece = board.get_piece(row, col)
                if piece != "." and piece.kind == PieceKind.KING:
                    if piece.color == PieceColor.WHITE:
                        white_king_exists = True
                    elif piece.color == PieceColor.BLACK:
                        black_king_exists = True

        # קביעת המנצח הרשמי על פי המלך ששרד על הלוח
        if white_king_exists and not black_king_exists:
            return "WHITE"
        if black_king_exists and not white_king_exists:
            return "BLACK"
            
        return None  # שני המלכים קיימים או שניהם חסרים, המשחק נמשך כרגיל