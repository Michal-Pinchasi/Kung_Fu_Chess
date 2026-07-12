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
        # Game Over
        if self.game_state.is_game_over:
            return ExecuteResult(False, "game_over")

        # Motion In Progress
        if self.arbiter.has_motion_on_path(source, destination):
            return ExecuteResult(False, "motion_in_progress")

        # Chess Rules
        validation = RuleEngine.validate_move(
            self.board,
            source,
            destination,
        )

        if not validation.is_valid:
            return ExecuteResult(False, validation.reason)

        piece = self.board.get_piece(source.row, source.col)

        # זמן התנועה = מספר המשבצות * 1000ms
        distance = max(
            abs(destination.row - source.row),
            abs(destination.col - source.col),
        )

        duration_ticks = distance * 10

        # הכלי נשאר על הלוח עד רגע ההגעה
        self.arbiter.start_motion(
            piece,
            source,
            destination,
            duration_ticks,
        )

        return ExecuteResult(True, "ok")

    def wait(self, ms: int):
        self.arbiter.advance_time(ms)

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