from Kung_Fu_Chess.model.board import Board

class BoardPrinter:
    @staticmethod
    def print_board(board: Board) -> str:
        lines = []
        for r in range(board.height):
            row_tokens = []
            for c in range(board.width):
                piece = board.get_piece(r, c)
                
                if piece == ".":
                    row_tokens.append(".")
                else:
                    # שימוש ב-.value של ה-Enum ישירות מתוך ה-Constants!
                    color_char = piece.color.value
                    kind_char = piece.kind.value
                    row_tokens.append(f"{color_char}{kind_char}")
            
            lines.append(" ".join(row_tokens))
            
        return "\n".join(lines)