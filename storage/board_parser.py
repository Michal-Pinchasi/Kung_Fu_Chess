from model.board import Board
from model.piece import Piece
from model.constants import PieceKind, PieceColor

class BoardParser:
    @staticmethod
    def parse(text: str) -> Board:
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
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
                
                if token == ".":
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