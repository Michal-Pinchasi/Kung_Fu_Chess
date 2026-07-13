from typing import List
from model.position import Position
from model.game_state import GameState
from rules.rule_engine import RuleEngine
from realtime.real_time_arbiter import RealTimeArbiter
from input.controller import Controller


class ExecuteResult:
    """Return value for any GameEngine command indicating acceptance and reason."""

    def __init__(self, is_accepted: bool, reason: str = "ok"):
        self.is_accepted = is_accepted
        self.reason = reason


class GameEngine:
    """Application-service coordinator for Kung Fu Chess.

    Coordinates Board, RuleEngine, and RealTimeArbiter. Enforces
    application-level guards (game_over, motion_in_progress) before
    delegating move legality to RuleEngine and motion scheduling to
    RealTimeArbiter.

    Does not contain piece-specific movement logic, pixel mapping,
    rendering code, or script parsing.
    """

    def __init__(self, board):
        self.board = board
        self.game_state = GameState(board)
        self.arbiter = RealTimeArbiter(board)
        self.controller = Controller(self)

    def request_move(self, source: Position, destination: Position) -> ExecuteResult:
        """Request a move from source to destination.

        Applies guards in order: game_over → motion_in_progress → rule validation.
        Schedules the motion through RealTimeArbiter only when all guards pass.
        """
        if self.game_state.is_game_over:
            return ExecuteResult(False, "game_over")

        if self.arbiter.has_motion_on_path(source, destination):
            return ExecuteResult(False, "motion_in_progress")

        validation = RuleEngine.validate_move(self.board, source, destination)
        if not validation.is_valid:
            return ExecuteResult(False, validation.reason)

        piece = self.board.get_piece(source.row, source.col)
        self.arbiter.schedule_move(piece, source, destination)
        return ExecuteResult(True, "ok")

    def request_jump(self, position: Position) -> ExecuteResult:
        """Request a defensive jump at position.

        Rejected when the game is over, the piece is already moving,
        or a jump is already active at that position.
        """
        if self.game_state.is_game_over:
            return ExecuteResult(False, "game_over")

        piece = self.board.get_piece(position.row, position.col)
        if piece == "." or piece is None:
            return ExecuteResult(False, "empty_source")

        if piece.state == "moving" or position in self.arbiter.status:
            return ExecuteResult(False, "motion_in_progress")

        self.arbiter.schedule_jump(piece, position)
        return ExecuteResult(True, "ok")

    def wait(self, ms: int) -> None:
        """Advance simulated time by ms milliseconds and process all arrivals.

        Handles four arrival categories returned by RealTimeArbiter:
        1. Intercepted moves (stopped by an enemy jump).
        2. Failed friendly moves (blocked by a friendly jump).
        3. Finished moves (normal landings with optional capture).
        4. Finished jumps (defensive jumps that completed).

        Sets game_over when a king is captured.
        """
        intercepted, finished_moves, finished_jumps, failed_friends = self.arbiter.advance_time(ms)
        captured_pieces = []

        for move in intercepted:
            self.board.remove_piece(move.frm.row, move.frm.col)
            move.piece.state = "captured"
            captured_pieces.append(move.piece)

        for move in failed_friends:
            move.piece.state = "idle"

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

        for jump in finished_jumps:
            jump.piece.state = "idle"

        if RuleEngine.check_king_capture(captured_pieces):
            self.game_state.is_game_over = True
            self.game_state.winner = RuleEngine.get_game_winner(self.board)

    def execute_command(self, command_str: str) -> None:
        """Forward a raw command string to the controller for parsing and dispatch."""
        self.controller.execute_command(command_str)
