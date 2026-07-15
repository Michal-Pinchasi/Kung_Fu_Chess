from dataclasses import dataclass
from typing import Optional
from model.position import Position
from model.game_state import GameState, GameSnapshot, PieceSnapshot
from rules.rule_engine import RuleEngine
from realtime.real_time_arbiter import RealTimeArbiter
from input.controller import Controller
from config.config_loader import EMPTY_SQUARE


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
    substitution in tests.

    Does not contain piece-specific movement logic, pixel mapping,
    rendering code, or script parsing.
    """

    def __init__(self, board, arbiter: Optional[RealTimeArbiter] = None):
        self.board = board
        self.game_state = GameState(board)
        self.arbiter = arbiter if arbiter is not None else RealTimeArbiter(board)
        self.controller = Controller(self)


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


    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """Request a move from source to destination.

        Applies guards in order: game_over → motion_in_progress → rule validation.
        Schedules the motion through RealTimeArbiter only when all guards pass.
        """
        if self.game_state.is_game_over:
            return MoveResult(False, "game_over")

        if self.arbiter.has_motion_on_path(source, destination):
            return MoveResult(False, "motion_in_progress")

        validation = RuleEngine.validate_move(self.board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        piece = self.board.get_piece(source.row, source.col)
        self.arbiter.schedule_move(piece, source, destination)
        return MoveResult(True, "ok")

    def request_jump(self, position: Position) -> MoveResult:
        """Request a defensive jump at position.

        Rejected when the game is over, the piece is already moving,
        or a jump is already active at that position.
        """
        if self.game_state.is_game_over:
            return MoveResult(False, "game_over")

        piece = self.board.get_piece(position.row, position.col)
        if piece == EMPTY_SQUARE or piece is None:
            return MoveResult(False, "empty_source")

        if piece.state == "moving" or position in self.arbiter.status:
            return MoveResult(False, "motion_in_progress")

        self.arbiter.schedule_jump(piece, position)
        return MoveResult(True, "ok")

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
            if target_piece is not None and target_piece != EMPTY_SQUARE:
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
                    pieces.append(PieceSnapshot(
                        id=piece.id,
                        kind=piece.kind.value,
                        color=piece.color.value,
                        x=float(c),
                        y=float(r),
                        state=piece.state,
                    ))
        return GameSnapshot(
            board_width=self.board.width,
            board_height=self.board.height,
            pieces=pieces,
            selected_cell=self.controller.selected_cell,
            game_over=self.game_state.is_game_over,
        )

    def click_at_window_pixel(self, px: int, py: int) -> None:
        """Translate a window pixel click into a board cell and forward to the controller."""
        from view.ui.layout.coordinate_mapper import CoordinateMapper
        result = CoordinateMapper.pixel_to_cell(px, py)
        print(f"[DEBUG] click px={px} py={py} -> cell={result}, selected={self.controller.selected_cell}")
        if result is None:
            self.controller.selected_cell = None
            return
        row, col = result
        self.controller.handle_click(Position(row, col))

    def execute_command(self, command_str: str) -> None:
        """Forward a raw command string to the controller for parsing and dispatch."""
        self.controller.execute_command(command_str)
