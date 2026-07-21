from dataclasses import dataclass
from typing import Optional
from model.position import Position
from model.game_state import GameState, GameSnapshot, PieceSnapshot
from model.move_history import MoveHistory
from model.score import Score
from rules.rule_engine import RuleEngine
from realtime.real_time_arbiter import RealTimeArbiter
from input.controller import Controller
from config.config_loader import EMPTY_SQUARE
from events.message_bus import MessageBus
from events.game_events import (
    MOVE_STARTED, JUMP_STARTED, MOVE_COMPLETED, SCORE_CHANGED, GAME_OVER,
    MoveStartedEvent, JumpStartedEvent, MoveCompletedEvent, ScoreChangedEvent, GameOverEvent,
)


@dataclass(frozen=True)
class MoveResult:
    """Immutable result returned by GameEngine for any move or command request."""
    is_accepted: bool
    reason: str = "ok"


class GameEngine:
    """Application-service coordinator for Kung Fu Chess.

    Coordinates Board, RuleEngine, and RealTimeArbiter. Enforces
    application-level guards (game_over, motion_in_progress) before
    delegating move legality to RuleEngine and motion scheduling to
    RealTimeArbiter.

    Supports dependency injection for RealTimeArbiter to allow easy
    substitution in tests. Also accepts an optional MessageBus: when
    provided, GameEngine publishes MOVE_STARTED/JUMP_STARTED/MOVE_COMPLETED/
    SCORE_CHANGED/GAME_OVER events (see events.game_events) at the moments
    they happen, without knowing or caring who — if anyone — is subscribed.
    When no bus is injected, publishing is a no-op and behavior is identical
    to before the bus existed.

    Does not contain piece-specific movement logic, pixel mapping,
    rendering code, or script parsing.
    """

    def __init__(
        self,
        board,
        arbiter: Optional[RealTimeArbiter] = None,
        message_bus: Optional[MessageBus] = None,
    ):
        self.board = board
        self.game_state = GameState(board)
        self.arbiter = arbiter if arbiter is not None else RealTimeArbiter(board)
        self.controller = Controller(self)
        self.move_history = MoveHistory()
        self.score = Score()
        self.bus = message_bus

    def _publish(self, event_type: str, payload=None) -> None:
        """Publish event_type via the injected message bus, if any (no-op otherwise).

        Lets GameEngine announce things happened (a move started/landed, the
        score changed, the game ended) without knowing or caring whether
        anything is actually listening.
        """
        if self.bus is not None:
            self.bus.publish(event_type, payload)


    def is_cell_empty(self, position: Position) -> bool:
        """Return True when the cell at position contains no piece."""
        piece = self.board.get_piece(position.row, position.col)
        return piece == EMPTY_SQUARE or piece is None

    def is_friendly_piece(self, position: Position, reference: Position) -> bool:
        """Return True when the piece at position has the same color as the piece at reference.

        Returns False when either cell is empty.
        """
        piece = self.board.get_piece(position.row, position.col)
        ref_piece = self.board.get_piece(reference.row, reference.col)
        if piece == EMPTY_SQUARE or piece is None:
            return False
        if ref_piece == EMPTY_SQUARE or ref_piece is None:
            return False
        return piece.color == ref_piece.color


    def _validate_pre_action(self, position: Position) -> tuple[bool, str, object]:
        """Helper: runs common checks before any action. Returns (is_valid, reason, piece)."""
        if self.game_state.is_game_over:
            return False, "game_over", None
            
        piece = self.board.get_piece(position.row, position.col)
        if piece == EMPTY_SQUARE or piece is None:
            return False, "empty_source", None
            
        if piece.state != "idle":
            return False, "motion_in_progress", piece
            
        return True, "ok", piece
    
    def request_move(self, source: Position, destination: Position) -> MoveResult:
        is_valid, reason, piece = self._validate_pre_action(source)
        if not is_valid: return MoveResult(False, reason)

        if self.arbiter.has_motion_on_path(destination, piece.color):
            return MoveResult(False, "motion_in_progress")
            
        validation = RuleEngine.validate_move(self.board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        self.arbiter.schedule_move(piece, source, destination)
        self._publish(MOVE_STARTED, MoveStartedEvent(
            piece_id=piece.id, kind=piece.kind.value, color=piece.color.value,
            source=source, destination=destination,
        ))
        return MoveResult(True, "ok")

    def request_jump(self, position: Position) -> MoveResult:
        is_valid, reason, piece = self._validate_pre_action(position)
        if not is_valid: return MoveResult(False, reason)

        if position in self.arbiter.status:
            return MoveResult(False, "motion_in_progress")

        self.arbiter.schedule_jump(piece, position)
        self._publish(JUMP_STARTED, JumpStartedEvent(
            piece_id=piece.id, kind=piece.kind.value, color=piece.color.value,
            position=position,
        ))
        return MoveResult(True, "ok")

    def wait(self, ms: int) -> None:
        """Advance simulated time by ms milliseconds and process all arrivals.

        Handles the arrival categories returned by RealTimeArbiter:
        1. Intercepted moves (stopped by an enemy jump).
        2. Failed friendly moves (blocked by a friendly jump).
        3. Finished moves (normal landings with optional capture) — the arbiter
           already put the piece into a long_rest cooldown.
        4. Finished jumps (defensive jumps that completed) — the arbiter already
           put the piece into a short_rest cooldown.
        5. Finished rests — the arbiter already returned the piece to idle;
           nothing further to do here.

        Credits each captured piece's point value to the capturing side's score,
        and sets game_over when a king is captured. Delegates to small private
        helpers, one per arrival category, so this method stays a thin
        orchestrator over arbiter results rather than doing the work itself.
        """
        intercepted, finished_moves, finished_jumps, finished_rests, failed_friends = self.arbiter.advance_time(ms)

        captured_pieces = self._process_intercepted(intercepted)
        self._process_failed_friends(failed_friends)
        self._process_finished_moves(finished_moves, captured_pieces)
        self._process_game_logic(captured_pieces)

    def _process_intercepted(self, intercepted_moves) -> list:
        """Mark each mid-flight-intercepted attacker as captured.

        Returns a new captured_pieces list, seeded with these attackers, for
        the caller to keep passing through the rest of this tick's processing.
        """
        captured_pieces = []
        for move in intercepted_moves:
            self.board.remove_piece(move.frm.row, move.frm.col)
            move.piece.state = "captured"
            captured_pieces.append(move.piece)
        return captured_pieces

    def _process_failed_friends(self, failed_friends) -> None:
        """Reset each move blocked by a friendly jump back to idle."""
        for move in failed_friends:
            move.piece.state = "idle"

    def _process_finished_moves(self, finished_moves, captured_pieces) -> None:
        """Apply board movement, capture, promotion, and move-history recording.

        Appends any piece captured on arrival to captured_pieces in place.
        """
        for move in finished_moves:
            # A different move earlier in this tick may have captured this
            # in-flight piece at its source. A captured piece must never land.
            if move.piece.state == "captured":
                self.arbiter.cancel_piece_activities(move.piece)
                continue
            self.board.remove_piece(move.frm.row, move.frm.col)

            target_piece = self.board.get_piece(move.to.row, move.to.col)
            is_capture = target_piece is not None and target_piece != EMPTY_SQUARE
            if is_capture:
                captured_pieces.append(target_piece)
                self.arbiter.cancel_piece_activities(target_piece)
                target_piece.state = "captured"
                self.board.remove_piece(move.to.row, move.to.col)

            RuleEngine.apply_post_arrival_rules(self.board, move.piece, move.to)
            self.board.set_piece(move.to.row, move.to.col, move.piece)

            self.move_history.add_move(
                move.piece.color.value, move.frm, move.to,
                move.piece.kind.value, is_capture
            )

            self._publish(MOVE_COMPLETED, MoveCompletedEvent(
                piece_id=move.piece.id, kind=move.piece.kind.value, color=move.piece.color.value,
                source=move.frm, destination=move.to, is_capture=is_capture,
            ))

    def _process_game_logic(self, captured_pieces) -> None:
        """Credit score for this tick's captures and check the win condition."""
        self._credit_captures(captured_pieces)

        if captured_pieces:
            self._publish(SCORE_CHANGED, ScoreChangedEvent(
                white_score=self.score.white_score, black_score=self.score.black_score,
            ))

        if RuleEngine.check_king_capture(captured_pieces):
            self.game_state.is_game_over = True
            self.game_state.winner = RuleEngine.get_capture_winner(captured_pieces)
            self._publish(GAME_OVER, GameOverEvent(winner=self.game_state.winner))

    def _credit_captures(self, captured_pieces) -> None:
        """Award score points for every piece captured this tick."""
        for piece in captured_pieces:
            self.score.credit_capture(piece)

    def snapshot(self) -> GameSnapshot:
        """Return a read-only snapshot of the current game state for the renderer.

        The snapshot contains piece positions, kinds, colors, states, and
        the game-over flag. It does not expose live Board or Piece objects.
        """
        pieces = []
        for r in range(self.board.height):
            for c in range(self.board.width):
                piece = self.board.get_piece(r, c)
                if piece != EMPTY_SQUARE and piece is not None:
                    x, y = float(c), float(r)
                    elapsed_state_ms = 0
                    if piece.state == "moving":
                        progress_info = self.arbiter.get_move_progress(piece)
                        if progress_info:
                            frm, to, progress = progress_info
                            x = frm.col + (to.col - frm.col) * progress
                            y = frm.row + (to.row - frm.row) * progress
                        elapsed_state_ms = self.arbiter.get_state_elapsed_ms(piece)
                    elif piece.state == "jump":
                        elapsed_state_ms = self.arbiter.get_state_elapsed_ms(piece)
                    pieces.append(PieceSnapshot(
                        id=piece.id,
                        kind=piece.kind.value,
                        color=piece.color.value,
                        x=x,
                        y=y,
                        state=piece.state,
                        elapsed_state_ms=elapsed_state_ms,
                    ))
        return GameSnapshot(
            board_width=self.board.width,
            board_height=self.board.height,
            pieces=pieces,
            selected_cell=self.controller.selected_cell,
            game_over=self.game_state.is_game_over,
            move_history=self.move_history,
            score=self.score,
        )
