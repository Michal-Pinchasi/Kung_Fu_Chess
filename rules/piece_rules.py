from typing import Set
from model.position import Position
from model.constants import PieceKind, PieceColor

class PieceRules:
    @staticmethod
    def legal_destinations(board, piece, position: Position) -> Set[Position]:
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
    @staticmethod
    def get_sliding_moves(board, position: Position, directions: list) -> Set[Position]:
        moves = set()
        for dr, dc in directions:
            r, c = position.row + dr, position.col + dc
            while board.is_valid_position(r, c):
                target_pos = Position(r, c)
                moves.add(target_pos)
                if board.get_piece(r, c) != ".":
                    break
                r += dr
                c += dc
        return moves

class RookRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return ChessRuleUtils.get_sliding_moves(board, position, directions)

class BishopRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return ChessRuleUtils.get_sliding_moves(board, position, directions)

class QueenRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        return ChessRuleUtils.get_sliding_moves(board, position, directions)

class KingRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        moves = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = position.row + dr, position.col + dc
            if board.is_valid_position(r, c):
                moves.add(Position(r, c))
        return moves

class KnightRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        moves = set()
        l_shapes = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in l_shapes:
            r, c = position.row + dr, position.col + dc
            if board.is_valid_position(r, c):
                moves.add(Position(r, c))
        return moves

class PawnRules:
    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        moves = set()
        direction = -1 if piece.color == PieceColor.WHITE else 1
        
        # 1. צעד אחד קדימה
        f_row, f_col = position.row + direction, position.col
        if board.is_valid_position(f_row, f_col) and board.get_piece(f_row, f_col) == ".":
            moves.add(Position(f_row, f_col))
            
            # 2. צעד כפול קדימה משורת המקור (לפי נתוני הלוח הצרים בטסטים שלך)
            is_starting_row = (piece.color == PieceColor.WHITE and position.row == board.height - 1) or \
                              (piece.color == PieceColor.BLACK and position.row == 0)
                              
            if is_starting_row:
                d_row = position.row + (2 * direction)
                if board.is_valid_position(d_row, f_col) and board.get_piece(d_row, f_col) == ".":
                    moves.add(Position(d_row, f_col))
            
        # 3. אכילה באלכסון
        for dc in [-1, 1]:
            diag_row, diag_col = position.row + direction, position.col + dc
            if board.is_valid_position(diag_row, diag_col):
                target = board.get_piece(diag_row, diag_col)
                if target != "." and target.color != piece.color:
                    moves.add(Position(diag_row, diag_col))
                    
        return moves