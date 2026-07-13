from typing import List, Tuple
from model.position import Position
from realtime.motion import PendingMove, PendingJump, Jumping
from config.config_loader import MILLISECONDS_PER_CELL, JUMP_DURATION_MILLISECONDS, TIME_STEP_MS


class RealTimeArbiter:
    """Manages all active motions and advances simulated game time.

    Responsibilities:
    - Schedule and track PendingMove and PendingJump objects.
    - Advance the internal clock in fixed time steps.
    - Resolve arrivals: normal landings, aerial interceptions, and
      friendly-fire blocked moves.

    Does not contain chess legality logic, click handling, or rendering.
    """

    def __init__(self, board):
        self.board = board
        self.pending = []
        self.status = {}
        self.clock_ms = 0

    def has_motion_on_path(self, source: Position, destination: Position) -> bool:
        """Return True when any active PendingMove conflicts with the given source or destination."""
        for activity in self.pending:
            if isinstance(activity, PendingMove):
                if (
                    activity.frm == source
                    or activity.to == destination
                    or activity.to == source
                    or activity.frm == destination
                ):
                    return True
        return False

    def schedule_move(self, piece, frm: Position, to: Position) -> PendingMove:
        """Create and register a PendingMove. Duration is proportional to Chebyshev distance."""
        distance = max(abs(to.row - frm.row), abs(to.col - frm.col))
        duration_ms = distance * MILLISECONDS_PER_CELL
        move = PendingMove(piece, frm, to, self.clock_ms + duration_ms)
        self.pending.append(move)
        piece.state = "moving"
        return move

    def schedule_jump(self, piece, pos: Position) -> PendingJump:
        """Create and register a defensive PendingJump at the given position."""
        jump = PendingJump(piece, pos, self.clock_ms + JUMP_DURATION_MILLISECONDS)
        self.status[pos] = Jumping(jump)
        self.pending.append(jump)
        piece.state = "moving"
        return jump

    def advance_time(self, ms: int) -> Tuple[
        List[PendingMove],
        List[PendingMove],
        List[PendingJump],
        List[PendingMove],
    ]:
        """Advance the clock by ms milliseconds and resolve all due motions.

        Returns a tuple of four lists:
        - intercepted_moves: moves stopped by an enemy jump at the destination.
        - finished_moves: moves that completed a normal landing.
        - finished_jumps: jumps that completed and released their cell.
        - failed_friend_moves: moves blocked by a friendly jump at the destination.
        """
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
                    if defender_status.jump.piece.color != move.piece.color:
                        intercepted_moves.append(move)
                    else:
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
