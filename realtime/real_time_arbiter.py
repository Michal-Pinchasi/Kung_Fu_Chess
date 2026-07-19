from typing import List, Optional, Tuple
from model.position import Position
from model.constants import PieceColor
from realtime.motion import PendingMove, PendingJump, Jumping, PendingRest
from config.config_loader import (
    MILLISECONDS_PER_CELL, JUMP_DURATION_MILLISECONDS, TIME_STEP_MS,
    LONG_REST_DURATION_MILLISECONDS, SHORT_REST_DURATION_MILLISECONDS,
)


class RealTimeArbiter:
    """Manages all active motions and advances simulated game time.

    Responsibilities:
    - Schedule and track PendingMove, PendingJump, and PendingRest objects.
    - Advance the internal clock in fixed time steps.
    - Resolve arrivals: normal landings, aerial interceptions, and
      friendly-fire blocked moves.
    - Automatically begin a post-action rest cooldown (long_rest after a
      landed move, short_rest after a completed jump) and release it back
      to idle when the cooldown elapses.

    Does not contain chess legality logic, click handling, or rendering.
    """

    def __init__(self, board):
        self.board = board
        self.pending = []
        self.status = {}
        self.clock_ms = 0

    def has_motion_on_path(self, destination: Position, color: PieceColor) -> bool:
        """Return True when a same-color piece is already pending to land on destination.

        This is the one collision RuleEngine.validate_move can't see on its own: it
        only checks the current board snapshot, not other in-flight pieces that
        haven't arrived yet. Two pieces of different colors are allowed to race to
        the same destination — whichever arrives first lands normally, and the later
        arrival captures it on landing (resolved naturally by advance_time against
        live board state). Only a same-color race to the same destination is blocked
        here.

        Every other square relationship — a target fleeing the square an attacker is
        inbound to, an attacker targeting a square another piece is mid-departure
        from, re-using an in-flight piece's own source — is governed by ordinary
        occupancy rules via validate_move against the live board (which doesn't
        change until a move actually resolves), or by the caller checking
        piece.state != "idle". Blocking them here too would wrongly prevent a piece
        from fleeing an incoming capture, which defeats the point of real-time play.
        """
        for activity in self.pending:
            if isinstance(activity, PendingMove):
                if activity.to == destination and activity.piece.color == color:
                    return True
        return False

    def _begin_rest(self, piece, duration_ms: int, state: str) -> PendingRest:
        """Schedule a post-action cooldown and mark the piece as resting."""
        rest = PendingRest(piece, self.clock_ms + duration_ms)
        self.pending.append(rest)
        piece.state = state
        return rest

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

    def _extract_due_activities(self) -> Tuple[List[PendingMove], List[PendingJump], List[PendingRest]]:
        """Split currently pending activities into those whose end_time_ms has arrived.

        Returns (due_moves, due_jumps, due_rests). Does not mutate self.pending —
        resolution and removal happen in the corresponding _resolve_due_* methods.
        """
        due_moves = []
        due_jumps = []
        due_rests = []

        for act in list(self.pending):
            if act.end_time_ms <= self.clock_ms:
                if isinstance(act, PendingMove):
                    due_moves.append(act)
                elif isinstance(act, PendingJump):
                    due_jumps.append(act)
                elif isinstance(act, PendingRest):
                    due_rests.append(act)

        return due_moves, due_jumps, due_rests

    def _resolve_due_moves(
        self, due_moves: List[PendingMove]
    ) -> Tuple[List[PendingMove], List[PendingMove], List[PendingMove]]:
        """Resolve each due move against the defensive-jump status at its destination.

        A move is intercepted (enemy jump present), blocked (friendly jump present),
        or lands normally — which begins a long_rest cooldown via _begin_rest. Removes
        each resolved move from self.pending. Returns
        (intercepted_moves, finished_moves, failed_friend_moves).
        """
        intercepted_moves = []
        finished_moves = []
        failed_friend_moves = []

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
                self._begin_rest(move.piece, LONG_REST_DURATION_MILLISECONDS, "long_rest")

        return intercepted_moves, finished_moves, failed_friend_moves

    def _resolve_due_jumps(self, due_jumps: List[PendingJump]) -> List[PendingJump]:
        """Release each due jump's cell status and begin a short_rest cooldown.

        Removes each resolved jump from self.pending. Returns finished_jumps.
        """
        finished_jumps = []

        for jump in due_jumps:
            finished_jumps.append(jump)
            self.status.pop(jump.pos, None)
            if jump in self.pending:
                self.pending.remove(jump)
            self._begin_rest(jump.piece, SHORT_REST_DURATION_MILLISECONDS, "short_rest")

        return finished_jumps

    def _resolve_due_rests(self, due_rests: List[PendingRest]) -> List[PendingRest]:
        """Return each due rest's piece to idle and remove it from self.pending.

        Returns finished_rests.
        """
        finished_rests = []

        for rest in due_rests:
            finished_rests.append(rest)
            rest.piece.state = "idle"
            if rest in self.pending:
                self.pending.remove(rest)

        return finished_rests

    def advance_time(self, ms: int) -> Tuple[
        List[PendingMove],
        List[PendingMove],
        List[PendingJump],
        List[PendingRest],
        List[PendingMove],
    ]:
        """Advance the clock by ms milliseconds and resolve all due motions.

        Returns a tuple of five lists:
        - intercepted_moves: moves stopped by an enemy jump at the destination.
        - finished_moves: moves that completed a normal landing (piece then begins
          a long_rest cooldown, scheduled internally).
        - finished_jumps: jumps that completed and released their cell (piece then
          begins a short_rest cooldown, scheduled internally).
        - finished_rests: cooldowns that completed; the piece is already back to
          "idle" by the time this returns.
        - failed_friend_moves: moves blocked by a friendly jump at the destination.
        """
        intercepted_moves = []
        finished_moves = []
        finished_jumps = []
        finished_rests = []
        failed_friend_moves = []

        target_time = self.clock_ms + ms

        while self.clock_ms < target_time:
            self.clock_ms += min(TIME_STEP_MS, target_time - self.clock_ms)

            due_moves, due_jumps, due_rests = self._extract_due_activities()

            tick_intercepted, tick_finished, tick_failed_friend = self._resolve_due_moves(due_moves)
            intercepted_moves.extend(tick_intercepted)
            finished_moves.extend(tick_finished)
            failed_friend_moves.extend(tick_failed_friend)

            finished_jumps.extend(self._resolve_due_jumps(due_jumps))
            finished_rests.extend(self._resolve_due_rests(due_rests))

        return intercepted_moves, finished_moves, finished_jumps, finished_rests, failed_friend_moves
