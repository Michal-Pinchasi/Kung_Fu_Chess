from typing import List
from model.position import Position
from model.game_state import GameState
from rules.rule_engine import RuleEngine
from realtime.real_time_arbiter import RealTimeArbiter
from input.controller import Controller

class ExecuteResult:
    def __init__(self, is_accepted: bool, reason: str = "ok"):
        self.is_accepted = is_accepted
        self.reason = reason

class GameEngine:
    def __init__(self, board):
        self.board = board
        self.game_state = GameState(board) 
        self.arbiter = RealTimeArbiter(board) 
        self.controller = Controller(self)

    def request_move(self, source: Position, destination: Position) -> ExecuteResult:
        if self.game_state.is_game_over: 
            return ExecuteResult(False, "game_over") 

        if self.arbiter.has_motion_on_path(source, destination): 
            return ExecuteResult(False, "motion_in_progress") 

        # בדיקת חוקיות מלאה (גיאומטריה, חסימות, כלי ידידותי ביעד)
        validation = RuleEngine.validate_move(self.board, source, destination)
        if not validation.is_valid:
            return ExecuteResult(False, validation.reason)

        piece = self.board.get_piece(source.row, source.col)
        self.arbiter.schedule_move(piece, source, destination)
        return ExecuteResult(True, "ok") 

    def request_jump(self, position: Position) -> ExecuteResult:
        if self.game_state.is_game_over:
            return ExecuteResult(False, "game_over")

        piece = self.board.get_piece(position.row, position.col)
        if piece == "." or piece is None:
            return ExecuteResult(False, "empty_source")

        if piece.state == "moving" or position in self.arbiter.status:
            return ExecuteResult(False, "motion_in_progress")

        self.arbiter.schedule_jump(piece, position)
        return ExecuteResult(True, "ok")

    def wait(self, ms: int):
        intercepted, finished_moves, finished_jumps, failed_friends = self.arbiter.advance_time(ms)
        captured_pieces = []

        # 1. עיבוד כלים שיורטו באוויר
        for move in intercepted:
            self.board.remove_piece(move.frm.row, move.frm.col)
            move.piece.state = "captured"
            captured_pieces.append(move.piece)

        # 2. עיבוד מהלכים שנכשלו מול כלי ידידותי באוויר
        for move in failed_friends:
            move.piece.state = "idle"

        # 3. עיבוד כלים שנחתו נחיתה רגילה על הקרקע
        for move in finished_moves:
            self.board.remove_piece(move.frm.row, move.frm.col)
            
            target_piece = self.board.get_piece(move.to.row, move.to.col)
            if target_piece is not None and target_piece != ".":
                captured_pieces.append(target_piece)
                target_piece.state = "captured"
                self.board.remove_piece(move.to.row, move.to.col)

            RuleEngine.apply_post_arrival_rules(self.board, move.piece, move.to)
            self.board.set_piece(move.to.row, move.to.col, move.piece)
            move.piece.state = "idle"

        # 4. החזרת כלים שסיימו קפיצה למצב פנוי
        for jump in finished_jumps:
            jump.piece.state = "idle"

        # 5. בדיקה מבוססת אירועי אכילה בלבד - הבדיקה הסורקת המיותרת הוסרה לחלוטין!
        if RuleEngine.check_king_capture(captured_pieces):
            self.game_state.is_game_over = True
            self.game_state.winner = RuleEngine.get_game_winner(self.board)
            return

    def execute_command(self, command_str: str):
        self.controller.execute_command(command_str)