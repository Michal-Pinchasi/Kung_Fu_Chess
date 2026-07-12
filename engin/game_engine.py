from model.position import Position
from model.game_state import GameState
from rules.rule_engine import RuleEngine
from realtime.real_time_arbiter import RealTimeArbiter

class ExecuteResult:
    def __init__(self, is_accepted: bool, reason: str = "ok"):
        self.is_accepted = is_accepted
        self.reason = reason

class GameEngine:
    def __init__(self, board):
        self.board = board
        self.game_state = GameState(board) 
        self.arbiter = RealTimeArbiter(board) 

    def request_move(self, source: Position, destination: Position) -> ExecuteResult:
        # 1. הגנה: האם המשחק כבר הסתיים?
        if self.game_state.is_game_over: 
            return ExecuteResult(False, "game_over") 

        # 2. הגנה: האם יש תנועה פעילה במסלול (לפי חוקי המסלול המשותף)?
        if self.arbiter.has_motion_on_path(source, destination): 
            return ExecuteResult(False, "motion_in_progress") 

        # 3. אימות חוקיות המהלך הסטטי מול מנוע החוקים
        validation = RuleEngine.validate_move(
            self.board,
            source,
            destination,
        ) 

        if not validation.is_valid: 
            return ExecuteResult(False, validation.reason) 

        piece = self.board.get_piece(source.row, source.col) 

        # 4. התחלת התנועה דרך הבורר בזמן אמת
        self.arbiter.start_motion(
            piece,
            source,
            destination,
        )

        return ExecuteResult(True, "ok") 

    def wait(self, ms: int):
        # 1. קידום הזמן וקבלת הכלים שנאכלו בפועל (Arrival Events) מה-Arbiter
        captured_pieces = self.arbiter.advance_time(ms)

        # 2. שימוש במתודה החדשה והגמישה ב-RuleEngine לבדיקת אכילת מלך
        if RuleEngine.check_king_capture(captured_pieces):
            self.game_state.is_game_over = True
            self.game_state.winner = RuleEngine.get_game_winner(self.board)
            return

        # 3. בדיקה משלימה וסטטית למקרה שהסיום נקבע אחרת
        winner = RuleEngine.get_game_winner(self.board) 
        if winner is not None: 
            self.game_state.is_game_over = True 
            self.game_state.winner = winner 

    def execute_command(self, command_str: str):
        parts = command_str.strip().split() 

        if not parts: 
            return

        cmd_type = parts[0].lower() 

        if cmd_type == "move": 
            try:
                src_parts = parts[1].split(",") 
                dst_parts = parts[3].split(",") 

                src = Position(int(src_parts[0]), int(src_parts[1])) 
                dst = Position(int(dst_parts[0]), int(dst_parts[1])) 

                self.request_move(src, dst) 

            except (IndexError, ValueError): 
                pass

        elif cmd_type == "wait": 
            try:
                ms = int(parts[1]) 
                self.wait(ms) 

            except (IndexError, ValueError): 
                pass