from model.constants import PieceColor
from config.config_loader import PIECE_VALUES


class Score:
    """Tracks each player's accumulated points, gained by capturing enemy pieces.

    Point values per piece kind come from config/constants.json — this class
    knows nothing about specific numbers, only how to look one up and which
    side to credit.
    """

    def __init__(self):
        self.white_score = 0
        self.black_score = 0

    def credit_capture(self, captured_piece) -> None:
        """Award points to the opponent of captured_piece's color, based on its kind."""
        points = PIECE_VALUES[captured_piece.kind.value]
        if captured_piece.color == PieceColor.WHITE:
            self.black_score += points
        else:
            self.white_score += points
