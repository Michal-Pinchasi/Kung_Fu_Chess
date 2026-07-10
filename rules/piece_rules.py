from model.position import Position
from model.constants import PieceKind, PieceColor

class PieceRules:
    """השער הראשי לחישוב יעדים גיאומטריים של כל הכלים (לקריאה בלבד)"""
    
    @staticmethod
    def legal_destinations(board, piece, position: Position) -> set[Position]:
        """החתימה הרשמית שנדרשה בסילבוס: מחזירה קבוצת מיקומים תיאורטית"""
        # מיפוי פשוט שמנתב כל כלי למחלקת החוקים הגיאומטרית שלו
        rule_map = {
            PieceKind.KING: KingRules,
            PieceKind.ROOK: RookRules,
            PieceKind.BISHOP: BishopRules,
            PieceKind.QUEEN: QueenRules,
            PieceKind.KNIGHT: KnightRules,
            PieceKind.PAWN: PawnRules,
        }
        
        rule_class = rule_map.get(piece.kind)
        if not rule_class:
            return set()
            
        return rule_class.get_moves(board, piece, position)


class ChessRuleUtils:
    """כלי עזר לחישוב מהיר של מהלכים קוויים (צריח, רץ, מלכה)"""
    @staticmethod
    def get_sliding_moves(board, position: Position, directions: list[tuple[int, int]]) -> set[Position]:
        moves = set()
        for dr, dc in directions:
            r, c = position.row + dr, position.col + dc
            # רצים בכיוון הקרן כל עוד אנחנו בתוך גבולות הלוח
            while board.is_valid_position(r, c):
                target_pos = Position(r, c)
                moves.add(target_pos)
                
                # אם פגשנו כלי (לא משנה של מי), הקרן נחסמת ואי אפשר להמשיך הלאה!
                if board.get_piece(r, c) != ".":
                    break
                r += dr
                c += dc
        return moves


# === מימושי חוקי התנועה הגיאומטריים לכל כלי בנפרד ===

class RookRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> set[Position]:
        # צריח זז ב-4 כיוונים ישרים (למעלה, למטה, ימינה, שמאלה)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return ChessRuleUtils.get_sliding_moves(board, position, directions)


class BishopRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> set[Position]:
        # רץ זז ב-4 כיווני אלכסון
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return ChessRuleUtils.get_sliding_moves(board, position, directions)


class QueenRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> set[Position]:
        # מלכה משלבת את כיווני הצריח והרץ ביחד
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        return ChessRuleUtils.get_sliding_moves(board, position, directions)


class KingRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> set[Position]:
        # מלך זז צעד אחד לכל 8 הכיוונים מסביבו
        moves = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = position.row + dr, position.col + dc
            if board.is_valid_position(r, c):
                moves.add(Position(r, c))
        return moves


class KnightRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> set[Position]:
        # פרש מדלג בצורת L (8 מיקומים אפשריים)
        moves = set()
        l_shapes = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in l_shapes:
            r, c = position.row + dr, position.col + dc
            if board.is_valid_position(r, c):
                moves.add(Position(r, c))
        return moves


class PawnRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> set[Position]:
        moves = set()
        # כיוון התנועה נקבע לפי צבע הרגלי (לבן עולה למעלה, שחור יורד למטה)
        direction = -1 if piece.color == PieceColor.WHITE else 1
        
        # 1. צעד אחד קדימה (חוקי גיאומטרית רק אם המשבצת מולו ריקה)
        f_row, f_col = position.row + direction, position.col
        if board.is_valid_position(f_row, f_col) and board.get_piece(f_row, f_col) == ".":
            moves.add(Position(f_row, f_col))
            
        # 2. אכילה באלכסון (חוקי גיאומטרית אם יש שם כלי אויב)
        for dc in [-1, 1]:
            diag_row, diag_col = position.row + direction, position.col + dc
            if board.is_valid_position(diag_row, diag_col):
                target = board.get_piece(diag_row, diag_col)
                if target != "." and target.color != piece.color:
                    moves.add(Position(diag_row, diag_col))
                    
        return moves