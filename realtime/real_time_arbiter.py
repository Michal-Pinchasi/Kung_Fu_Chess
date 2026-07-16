from typing import List, Optional, Tuple
from model.position import Position
from model.constants import PieceColor
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

    def has_motion_on_path(self, source: Position, destination: Position, color: PieceColor) -> bool:
        """Return True when any active PendingMove conflicts with the given source or destination.

        Two pieces of different colors are allowed to race to the same destination —
        whichever arrives first lands normally, and the later arrival captures it on
        landing (resolved naturally by advance_time against live board state). Only a
        same-color race to the same destination is blocked here; re-using an in-flight
        piece's own source, or targeting a square another pending move is departing
        from/to, is always blocked regardless of color.
        """
        for activity in self.pending:
            if isinstance(activity, PendingMove):
                if activity.frm == source:
                    return True
                if activity.to == destination and activity.piece.color == color:
                    return True
                if activity.to == source or activity.frm == destination:
                    return True
        return False

    @staticmethod
    def _move_duration_ms(frm: Position, to: Position) -> int:
        """Travel duration for a move: Chebyshev distance × MILLISECONDS_PER_CELL."""
        distance = max(abs(to.row - frm.row), abs(to.col - frm.col))
        return distance * MILLISECONDS_PER_CELL

    def schedule_move(self, piece, frm: Position, to: Position) -> PendingMove:
        """Create and register a PendingMove. Duration is proportional to Chebyshev distance."""
        duration_ms = self._move_duration_ms(frm, to)
        move = PendingMove(piece, frm, to, self.clock_ms + duration_ms)
        self.pending.append(move)
        piece.state = "moving"
        return move

    def schedule_jump(self, piece, pos: Position) -> PendingJump:
        """Create and register a defensive PendingJump at the given position."""
        jump = PendingJump(piece, pos, self.clock_ms + JUMP_DURATION_MILLISECONDS)
        self.status[pos] = Jumping(jump)
        self.pending.append(jump)
        piece.state = "jump"
        return jump

    def get_move_progress(self, piece) -> Optional[Tuple[Position, Position, float]]:
        """Return (frm, to, progress 0..1) for piece's active PendingMove, or None."""
        for act in self.pending:
            if isinstance(act, PendingMove) and act.piece is piece:
                duration_ms = self._move_duration_ms(act.frm, act.to)
                if duration_ms <= 0:
                    return act.frm, act.to, 1.0
                elapsed = duration_ms - (act.end_time_ms - self.clock_ms)
                progress = max(0.0, min(1.0, elapsed / duration_ms))
                return act.frm, act.to, progress
        return None

    def get_state_elapsed_ms(self, piece) -> int:
        """Elapsed ms since piece's current PendingMove/PendingJump started (0 if none active)."""
        for act in self.pending:
            if act.piece is piece:
                if isinstance(act, PendingMove):
                    duration_ms = self._move_duration_ms(act.frm, act.to)
                else:
                    duration_ms = JUMP_DURATION_MILLISECONDS
                return max(0, duration_ms - (act.end_time_ms - self.clock_ms))
        return 0

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
            self.clock_ms += min(TIME_STEP_MS, target_time - self.clock_ms)

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
