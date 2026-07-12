from model.board import Board
from model.piece import Piece
from model.position import Position
from model.constants import PieceKind, PieceColor

class TextBoardSerializer:
    @staticmethod
    def parse(input_text: str) -> Board:
        lines = input_text.strip().split("\n")
        
        # מוצאים את גודל הלוח לפי השורות הראשונות
        board_lines = []
        for line in lines:
            if line.startswith("Commands:"):
                break
            if line.strip() and not line.startswith("Board:"):
                board_lines.append(line.strip().split())
        
        height = len(board_lines)
        width = len(board_lines[0]) if height > 0 else 0
        board = Board(width, height)
        
        # מונים כדי לייצר מזהה ייחודי (id) לכל סוג כלי
        counters = {}
        
        for r in range(height):
            for c in range(width):
                cell_text = board_lines[r][c]
                if cell_text == ".":
                    continue
                
                # פענוח צבע וסוג הכלי מהטקסט (למשל: "wR" -> לבן, צריח)
                color = PieceColor.WHITE if cell_text[0] == "w" else PieceColor.BLACK
                kind_char = cell_text[1]
                
                if kind_char == "R":
                    kind = PieceKind.ROOK
                elif kind_char == "K":
                    kind = PieceKind.KING
                elif kind_char == "P":
                    kind = PieceKind.PAWN
                elif kind_char == "N":
                    kind = PieceKind.KNIGHT
                elif kind_char == "B":
                    kind = PieceKind.BISHOP
                elif kind_char == "Q":
                    kind = PieceKind.QUEEN
                
                # יצירת מזהה ייחודי אוטומטי (למשל: "w_R_1")
                key = f"{cell_text[0]}_{kind_char}"
                counters[key] = counters.get(key, 0) + 1
                piece_id = f"{key}_{counters[key]}"
                
                # יצירת הכלי עם ה-id החדש והמסונכרן!
                piece = Piece(id=piece_id, kind=kind, color=color)
                board.add_piece(r, c, piece)
                
        return board