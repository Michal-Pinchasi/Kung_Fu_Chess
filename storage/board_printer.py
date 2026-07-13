from model.board import Board


class BoardPrinter:
    """Converts a Board's logical occupancy into a human-readable text representation."""

    @staticmethod
    def print_board(board: Board) -> str:
        """Return a multi-line string representing the current board state.

        Each row is space-separated. Empty cells are shown as '.'.
        Occupied cells are shown as two-character tokens, e.g. 'wR' or 'bK'.
        """
        lines = []
        for r in range(board.height):
            row_tokens = []
            for c in range(board.width):
                piece = board.get_piece(r, c)
                if piece == ".":
                    row_tokens.append(".")
                else:
                    row_tokens.append(f"{piece.color.value}{piece.kind.value}")
            lines.append(" ".join(row_tokens))
        return "\n".join(lines)
