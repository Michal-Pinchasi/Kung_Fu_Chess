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
        if not board.is_valid_position(source.row, source.col):
            return ValidationResult(False, "outside_board")

        piece = board.get_piece(source.row, source.col)
        
        if piece == ".":
            return ValidationResult(False, "empty_source")
            
        if not board.is_valid_position(destination.row, destination.col):
            return ValidationResult(False, "outside_board")
            
        target_piece = board.get_piece(destination.row, destination.col)
        
        if target_piece != "." and target_piece.color == piece.color:
            return ValidationResult(False, "friendly_destination")
            
        legal_destinations = PieceRules.legal_destinations(board, piece, source)
        if destination not in legal_destinations:
            return ValidationResult(False, "illegal_piece_move")
            
        return ValidationResult(True, "ok")

    @staticmethod
    def apply_post_arrival_rules(board, piece, destination: Position):
        """
        שכבת החוקים קובעת האם חלים חוקים מיוחדים על הכלי ברגע הנחיתה שלו.
        כאן ממומש חוק ההכתרה (Promotion) של רגלי בצורה גמישה ומרוכזת.
        """
        if piece.kind == PieceKind.PAWN:
            if (piece.color == PieceColor.WHITE and destination.row == 0) or \
               (piece.color == PieceColor.BLACK and destination.row == board.height - 1):
                piece.kind = PieceKind.QUEEN

    @staticmethod
    def check_king_capture(captured_pieces) -> bool:
        """
        מקבלת רשימת כלים שנאכלו ומחזירה True אם אחד מהם הוא מלך.
        בדיקה זו משאירה את ההחלטה על משמעות הכלים בשכבת החוקים.
        """
        for piece in captured_pieces:
            if piece != "." and piece.kind == PieceKind.KING:
                return True
        return False

    @staticmethod
    def get_game_winner(board) -> str or None:
        """
        סורק את הלוח ומזהה האם אחד המלכים חסר (חוסל).
        אם המלך השחור חסר -> הלבן מנצח ("WHITE").
        אם המלך הלבן חסר -> השחור מנצח ("BLACK").
        """
        white_king_exists = False
        black_king_exists = False

        for row in range(board.height):
            for col in range(board.width):
                piece = board.get_piece(row, col)
                if piece != "." and piece.kind == PieceKind.KING:
                    if piece.color == PieceColor.WHITE:
                        white_king_exists = True
                    elif piece.color == PieceColor.BLACK:
                        black_king_exists = True

        if white_king_exists and not black_king_exists:
            return "WHITE"
        if black_king_exists and not white_king_exists:
            return "BLACK"
            
        return None