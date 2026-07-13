from typing import List, Tuple
from model.position import Position
from realtime.motion import PendingMove, PendingJump, Jumping
from config.constants import MILLISECONDS_PER_CELL, JUMP_DURATION_MILLISECONDS, TIME_STEP_MS

class RealTimeArbiter:
    def __init__(self, board):
        self.board = board
        self.pending = []
        self.status = {}
        self.clock_ms = 0

    def has_motion_on_path(self, source: Position, destination: Position) -> bool:
        for activity in self.pending:
            if isinstance(activity, PendingMove):
                if (activity.frm == source or activity.to == destination or
                    activity.to == source or activity.frm == destination):
                    return True
        return False

    def schedule_move(self, piece, frm: Position, to: Position) -> PendingMove:
        distance = max(abs(to.row - frm.row), abs(to.col - frm.col))
        duration_ms = distance * MILLISECONDS_PER_CELL

        move = PendingMove(piece, frm, to, self.clock_ms + duration_ms)
        self.pending.append(move)
        piece.state = "moving"
        return move

    def schedule_jump(self, piece, pos: Position) -> PendingJump:
        jump = PendingJump(piece, pos, self.clock_ms + JUMP_DURATION_MILLISECONDS)
        self.status[pos] = Jumping(jump)
        self.pending.append(jump)
        piece.state = "moving"
        return jump

    def advance_time(self, ms: int) -> Tuple[List[PendingMove], List[PendingMove], List[PendingJump], List[PendingMove]]:
        """מחזיר גם מהלכים שבוטלו עקב חסימת ידיד (failed_friend_moves)"""
        intercepted_moves = []
        finished_moves = []
        finished_jumps = []
        failed_friend_moves = []

        target_time = self.clock_ms + ms

        while self.clock_ms < target_time:
            self.clock_ms += TIME_STEP_MS

            due_moves = []
            due_jumps = []

            for act in list(self.pending):
                if act.end_time_ms <= self.clock_ms:
                    if isinstance(act, PendingMove):
                        due_moves.append(act)
                    elif isinstance(act, PendingJump):
                        due_jumps.append(act)

            for move in due_moves:
                defender_status = self.status.get(move.to)

                if defender_status and isinstance(defender_status, Jumping):
                    # הגנה אווירית מופעלת אך ורק אם מדובר בכלי אויב! (טסט 6)
                    if defender_status.jump.piece.color != move.piece.color:
                        intercepted_moves.append(move)
                    else:
                        # אם זה כלי ידידותי באוויר, המהלך נכשל והכלי המגיע נשאר במקומו המקורי
                        failed_friend_moves.append(move)

                    if move in self.pending:
                        self.pending.remove(move)
                else:
                    finished_moves.append(move)

                    if move in self.pending:
                        self.pending.remove(move)

            for jump in due_jumps:
                finished_jumps.append(jump)
                self.status.pop(jump.pos, None)

                if jump in self.pending:
                    self.pending.remove(jump)

        return intercepted_moves, finished_moves, finished_jumps, failed_friend_moves