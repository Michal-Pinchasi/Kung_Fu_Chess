from model.position import Position
from model.constants import PieceKind, PieceColor
from rules.piece_rules import PieceRules
from config.config_loader import EMPTY_SQUARE
from typing import Optional


class ValidationResult:
    """The result of a static legality check performed by RuleEngine."""

    def __init__(self, is_valid: bool, reason: str = "ok"):
        self.is_valid = is_valid
        self.reason = reason


class RuleEngine:
    """Stateless validation service for chess move legality.

    All methods are read-only with respect to Board. RuleEngine inspects
    board state and returns a ValidationResult but never mutates pieces,
    moves pieces, or updates game-over state.
    """

    @staticmethod
    def validate_move(board, source: Position, destination: Position) -> ValidationResult:
        """Check whether a move from source to destination is currently legal.

        Validation order:
        1. Source must be inside the board.
        2. Source must not be empty.
        3. Destination must be inside the board.
        4. Destination must not be occupied by a friendly piece.
        5. Destination must appear in the piece's legal destinations.

        Returns a ValidationResult with is_valid=True and reason="ok" on success,
        or is_valid=False with a stable machine-readable reason on failure.
        """
        if not board.is_valid_position(source.row, source.col):
            return ValidationResult(False, "outside_board")

        piece = board.get_piece(source.row, source.col)

        if piece == EMPTY_SQUARE:
            return ValidationResult(False, "empty_source")

        if not board.is_valid_position(destination.row, destination.col):
            return ValidationResult(False, "outside_board")

        target_piece = board.get_piece(destination.row, destination.col)

        if target_piece != EMPTY_SQUARE and target_piece.color == piece.color:
            return ValidationResult(False, "friendly_destination")

        legal_destinations = PieceRules.legal_destinations(board, piece, source)
        if destination not in legal_destinations:
            return ValidationResult(False, "illegal_piece_move")

        return ValidationResult(True, "ok")

    @staticmethod
    def apply_post_arrival_rules(board, piece, destination: Position) -> None:
        """Apply any special rules triggered when a piece lands on its destination.

        Currently implements pawn promotion: a pawn that reaches the far rank
        is promoted to a queen.
        """
        if piece.kind == PieceKind.PAWN:
            if (piece.color == PieceColor.WHITE and destination.row == 0) or (
                piece.color == PieceColor.BLACK and destination.row == board.height - 1
            ):
                piece.kind = PieceKind.QUEEN

    @staticmethod
    def check_king_capture(captured_pieces) -> bool:
        """Return True when any piece in captured_pieces is a king."""
        for piece in captured_pieces:
            if piece != EMPTY_SQUARE and piece.kind == PieceKind.KING:
                return True
        return False

    @staticmethod
    def get_game_winner(board) -> Optional[str]:
        """Scan the board and return the winner based on which king is missing.

        Returns "WHITE" when the black king is absent,
        "BLACK" when the white king is absent, or None when both kings are present.
        """
        white_king_exists = False
        black_king_exists = False

        for row in range(board.height):
            for col in range(board.width):
                piece = board.get_piece(row, col)
                if piece != EMPTY_SQUARE and piece.kind == PieceKind.KING:
                    if piece.color == PieceColor.WHITE:
                        white_king_exists = True
                    elif piece.color == PieceColor.BLACK:
                        black_king_exists = True

        if white_king_exists and not black_king_exists:
            return "WHITE"
        if black_king_exists and not white_king_exists:
            return "BLACK"

        return None