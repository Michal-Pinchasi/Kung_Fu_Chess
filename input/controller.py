from model.position import Position
from input.board_mapper import BoardMapper

class Controller:
    def __init__(self, game_engine):
        self.engine = game_engine
        self.board = game_engine.board
        self.selected_cell = None

    def click(self, x: int, y: int):
        pos = BoardMapper.pixel_to_cell(x, y, self.board.width, self.board.height)
        if pos is not None:
            self.handle_click(pos)

    def handle_click(self, position: Position):
        if self.engine.game_state.is_game_over:
            return

        piece = self.board.get_piece(position.row, position.col)

        if self.selected_cell is None:
            if piece != "." and piece is not None:
                self.selected_cell = position
            return

        src = self.selected_cell
        self.selected_cell = None

        # אם לחצו על כלי ידידותי — בחירה מחדש במקום ניסיון מהלך
        if piece != "." and piece is not None:
            src_piece = self.board.get_piece(src.row, src.col)
            if src_piece != "." and src_piece is not None and piece.color == src_piece.color:
                self.selected_cell = position
                return

        if src != position:
            self.engine.request_move(src, position)

    def execute_command(self, command_str: str):
        parts = command_str.strip().split() 
        if not parts: 
            return

        cmd_type = parts[0].lower() 

        if cmd_type == "click":
            try:
                pixel_x = int(parts[1])
                pixel_y = int(parts[2])
                self.click(pixel_x, pixel_y)
            except (IndexError, ValueError): 
                pass

        elif cmd_type == "jump":
            try:
                pixel_x = int(parts[1])
                pixel_y = int(parts[2])
                pos = BoardMapper.pixel_to_cell(pixel_x, pixel_y, self.board.width, self.board.height)
                if pos is not None:
                    self.engine.request_jump(pos)
            except (IndexError, ValueError):
                pass

        elif cmd_type == "wait": 
            try:
                ms = int(parts[1]) 
                self.engine.wait(ms)
            except (IndexError, ValueError): 
                pass