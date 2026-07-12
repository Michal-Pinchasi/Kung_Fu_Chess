from model.position import Position
from input.board_mapper import BoardMapper

class Controller:
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.selected_cell = None 

    def click(self, x: int, y: int):
        width = self.game_engine.board.width
        height = self.game_engine.board.height
        
        clicked_pos = BoardMapper.pixel_to_cell(x, y, width, height)

        if self.selected_cell is None:
            if clicked_pos is None:
                return
            piece = self.game_engine.board.get_piece(clicked_pos.row, clicked_pos.col)
            if piece != ".":
                self.selected_cell = clicked_pos 
        else:
            if clicked_pos is None:
                self.selected_cell = None
                return
            
            current_piece = self.game_engine.board.get_piece(self.selected_cell.row, self.selected_cell.col)
            clicked_piece = self.game_engine.board.get_piece(clicked_pos.row, clicked_pos.col)
            
            if clicked_piece != "." and hasattr(current_piece, 'color') and hasattr(clicked_piece, 'color') and current_piece.color == clicked_piece.color:
                self.selected_cell = clicked_pos
                return
                
            self.game_engine.request_move(self.selected_cell, clicked_pos)
            self.selected_cell = None