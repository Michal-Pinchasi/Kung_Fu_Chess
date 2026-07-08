import sys
from entities.board import Board
from entities.piece import Piece
from entities.strategies import STRATEGIES_MAP

class TextBoardSerializer:
    VALID_PIECES = {"K", "Q", "R", "B", "N", "P"}
    VALID_COLORS = {"w", "b"}

    @staticmethod
    def validate_token(token: str):
        if token == ".":
            return True
        if len(token) == 2 and token[0] in TextBoardSerializer.VALID_COLORS and token[1] in TextBoardSerializer.VALID_PIECES:
            return True
        print("ERROR UNKNOWN_TOKEN")
        sys.exit(0)

    @staticmethod
    def parse(input_text: str) -> Board:
        lines = [line.strip() for line in input_text.strip().split("\n") if line.strip()]
        board_lines = []
        in_board_section = False
        
        for line in lines:
            if line.startswith("Board:"):
                in_board_section = True
                continue
            if line.startswith("Commands:"):
                break
            if in_board_section:
                board_lines.append(line)

        if not board_lines:
            print("ERROR ROW_WIDTH_MISMATCH")
            sys.exit(0)

        height = len(board_lines)
        width = len(board_lines[0].split())
        board = Board(width, height)

        for row_idx, line in enumerate(board_lines):
            tokens = line.split()
            if len(tokens) != width:
                print("ERROR ROW_WIDTH_MISMATCH")
                sys.exit(0)
            
            for col_idx, token in enumerate(tokens):
                TextBoardSerializer.validate_token(token)
                if token == ".":
                    board.set_piece(row_idx, col_idx, ".")
                else:
                    color = token[0]
                    role = token[1]
                    strategy = STRATEGIES_MAP[role]  # שליפת האסטרטגיה המתאימה
                    # הזרקת האסטרטגיה ליצירת ה-Piece
                    piece_obj = Piece(color, role, strategy)
                    board.set_piece(row_idx, col_idx, piece_obj)
        return board

    @staticmethod
    def serialize(board: Board) -> str:
        result_rows = []
        for row in board.grid:
            row_strings = []
            for item in row:
                if item == ".":
                    row_strings.append(".")
                else:
                    # שחזור הטוקן הטקסטואלי מתוך תכונות ה-Piece
                    row_strings.append(f"{item.color}{item.role}")
            result_rows.append(" ".join(row_strings))
        return "\n".join(result_rows)