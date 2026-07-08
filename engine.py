from board import Board
from position import Position
from serializer import TextBoardSerializer

class ActiveMove:
    def __init__(self, from_pos: Position, to_pos: Position, piece: str, remaining_ms: int):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece = piece
        self.remaining_ms = remaining_ms

class GameEngine:
    CELL_SIZE_PIXELS = 100
    def __init__(self, board: Board):
        self.board = board
        self.selected_pos = None
        self.active_moves = []
        self.DEFAULT_MOVE_DURATION = 1000 

    def execute_command(self, cmd_text: str):
        """פונקציה מרכזית שמקבלת פקודה ומנתבת אותה - מנקה את ה-Main!"""
        if cmd_text.startswith("click"):
            parts = cmd_text.split()
            if len(parts) == 3:
                self.handle_click(int(parts[1]), int(parts[2]))
                
        elif cmd_text.startswith("wait"):
            parts = cmd_text.split()
            if len(parts) == 2:
                self.advance_time(int(parts[1]))
                
        elif cmd_text == "print board":
            canonical_board = TextBoardSerializer.serialize(self.board)
            print(canonical_board)

    def handle_click(self, x: int, y: int):
        col = x // CELL_SIZE_PIXELS
        row = y // CELL_SIZE_PIXELS

        if not self.board.is_valid_position(row, col):
            return

        clicked_piece = self.board.get_piece(row, col)
        current_click_pos = Position(row, col)

        if self.selected_pos is None:
            if clicked_piece != ".":
                self.selected_pos = current_click_pos
            return

        selected_piece = self.board.get_piece(self.selected_pos.row, self.selected_pos.col)
        
        if clicked_piece != "." and clicked_piece[0] == selected_piece[0]:
            self.selected_pos = current_click_pos
        else:
            self.request_move(self.selected_pos, current_click_pos, selected_piece)
            self.selected_pos = None 

    def request_move(self, from_pos: Position, to_pos: Position, piece: str):
        if from_pos == to_pos:
            return
        self.board.set_piece(from_pos.row, from_pos.col, ".")
        new_move = ActiveMove(from_pos, to_pos, piece, self.DEFAULT_MOVE_DURATION)
        self.active_moves.append(new_move)

    def advance_time(self, ms: int):
        completed_moves = []
        for move in self.active_moves:
            move.remaining_ms -= ms
            if move.remaining_ms <= 0:
                completed_moves.append(move)

        for move in completed_moves:
            self.board.set_piece(move.to_pos.row, move.to_pos.col, move.piece)
            self.active_moves.remove(move)