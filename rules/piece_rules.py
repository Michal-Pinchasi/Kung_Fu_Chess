from typing import Set
from model.position import Position
from model.constants import PieceKind, PieceColor
from config.config_loader import EMPTY_SQUARE


class PieceRules:
    """Entry point for computing legal destinations for any piece type.

    Dispatches to the appropriate rule class based on piece.kind.
    Returns an empty set for unknown piece types.
    """

    @staticmethod
    def legal_destinations(board, piece, position: Position) -> Set[Position]:
        """Return the set of legal destination cells for piece at position."""
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
    """Shared utilities for sliding piece movement."""

    @staticmethod
    def get_sliding_moves(board, piece, position: Position, directions: list) -> Set[Position]:
        """Slide outward in each direction until blocked.

        Enemy-occupied cells are included as capturable destinations.
        Friendly-occupied cells stop the slide without being included.
        """
        moves = set()
        for dr, dc in directions:
            r, c = position.row + dr, position.col + dc
            while board.is_valid_position(r, c):
                target = board.get_piece(r, c)
                if target != EMPTY_SQUARE:
                    if target.color != piece.color:
                        moves.add(Position(r, c))
                    break
                moves.add(Position(r, c))
                r += dr
                c += dc
        return moves


class RookRules:
    """Movement rules for the rook: horizontal and vertical sliding."""

    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return ChessRuleUtils.get_sliding_moves(board, piece, position, directions)


class BishopRules:
    """Movement rules for the bishop: diagonal sliding."""

    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return ChessRuleUtils.get_sliding_moves(board, piece, position, directions)


class QueenRules:
    """Movement rules for the queen: combines rook and bishop movement."""

    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        return ChessRuleUtils.get_sliding_moves(board, piece, position, directions)


class KingRules:
    """Movement rules for the king: one step in any direction."""

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
    """Movement rules for the knight: L-shaped jumps, ignoring all blockers."""

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
    """Movement rules for the pawn.

    - White pawns move downward (increasing row index in our UI layout).
    - Black pawns move upward (decreasing row index in our UI layout).
    - One step forward is legal only when the destination is empty.
    - Two steps forward from the starting row is legal only when both
      intermediate and destination cells are empty.
    - Diagonal capture is legal only when an enemy piece occupies the target.
    """

    @staticmethod
    def get_moves(board, piece, position: Position) -> Set[Position]:
        moves = set()
        
        # שינוי כאן: לבן זז פלוס 1 (למטה), שחור זז מינוס 1 (למעלה)
        direction = 1 if piece.color == PieceColor.WHITE else -1

        f_row, f_col = position.row + direction, position.col
        if board.is_valid_position(f_row, f_col) and board.get_piece(f_row, f_col) == EMPTY_SQUARE:
            moves.add(Position(f_row, f_col))

            # שינוי כאן: שורת ההתחלה של לבן היא 1 (למעלה), ושל שחור היא 6 (למטה, שזה board.height - 2)
            is_starting_row = (
                (piece.color == PieceColor.WHITE and position.row == 1)
                or (piece.color == PieceColor.BLACK and position.row == board.height - 2)
            )
            if is_starting_row:
                d_row = position.row + (2 * direction)
                if board.is_valid_position(d_row, f_col) and board.get_piece(d_row, f_col) == EMPTY_SQUARE:
                    moves.add(Position(d_row, f_col))

        for dc in [-1, 1]:
            diag_row, diag_col = position.row + direction, position.col + dc
            if board.is_valid_position(diag_row, diag_col):
                target = board.get_piece(diag_row, diag_col)
                if target != EMPTY_SQUARE and target.color != piece.color:
                    moves.add(Position(diag_row, diag_col))

        return moves