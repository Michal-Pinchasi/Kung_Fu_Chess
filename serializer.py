import sys
from board import Board

class TextBoardSerializer:
    VALID_PIECES = {"K", "Q", "R", "B", "N", "P"}  # מלך, מלכה, צריח, רץ, פרש, רגלי
    VALID_COLORS = {"w", "b"}

    @staticmethod
    def validate_token(token: str):
        """בודק אם הטוקן הוא נקודה או כלי חוקי (למשל wK)"""
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
        first_row_tokens = board_lines[0].split()
        width = len(first_row_tokens)

        board = Board(width, height)

        for row_idx, line in enumerate(board_lines):
            tokens = line.split()
            if len(tokens) != width:
                print("ERROR ROW_WIDTH_MISMATCH")
                sys.exit(0)
            
            for col_idx, token in enumerate(tokens):
                TextBoardSerializer.validate_token(token)
                board.set_piece(row_idx, col_idx, token)

        return board

    @staticmethod
    def serialize(board: Board) -> str:
        """ממיר את הלוח חזרה לפורמט קנוני מדויק"""
        result_rows = []
        for row in board.grid:
            result_rows.append(" ".join(row))
        return "\n".join(result_rows)