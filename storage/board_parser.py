from model.board import Board
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from config.constants import EMPTY_SQUARE


class BoardParser:
    """Parses a textual board description into a Board object.

    Expected format: rows separated by newlines, cells separated by spaces.
    Each cell is either EMPTY_SQUARE ('.') or a two-character token such as
    'wK' (white king) or 'bR' (black rook).

    Raises ValueError on inconsistent row lengths or unknown piece tokens.
    """

    @staticmethod
    def parse(text: str) -> Board:
        """Parse text into a Board. Raises ValueError on invalid input."""
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        if not lines:
            raise ValueError("Board text cannot be empty")

        grid_tokens = [line.split() for line in lines]
        height = len(grid_tokens)
        width = len(grid_tokens[0])

        for row_tokens in grid_tokens:
            if len(row_tokens) != width:
                raise ValueError("Inconsistent row lengths in board definition")

        board = Board(width, height)
        piece_counter = 0

        for r in range(height):
            for c in range(width):
                token = grid_tokens[r][c]

                if token == EMPTY_SQUARE:
                    continue

                if len(token) != 2:
                    raise ValueError(f"Invalid piece token: {token}")

                color_char, kind_char = token[0], token[1]

                try:
                    color = PieceColor(color_char)
                    kind = PieceKind(kind_char)
                except ValueError:
                    raise ValueError(f"Unknown piece token: {token}")

                piece_id = f"{token}_{piece_counter}"
                piece_counter += 1
                piece = Piece(id=piece_id, kind=kind, color=color)
                board.add_piece(r, c, piece)

        return board
