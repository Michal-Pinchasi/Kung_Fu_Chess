"""
Parses wire-format command strings sent by network clients into typed
move/jump command objects.

Wire formats (fixed-width, unambiguous by length/trailing character):
    Move: <Color><Kind><FromFile><FromRank><ToFile><ToRank>   e.g. "WQe2e5" (6 chars)
    Jump: <Color><Kind><File><Rank>J                            e.g. "WKe2J"  (5 chars, trailing literal 'J')

Color is 'W' or 'B'. Kind is one of K, Q, R, B, N, P (matching
model.constants.PieceKind values). Squares use standard algebraic notation
(file a-h, rank a positive digit), consistent with the rank = row + 1
convention already used by view.ui.rendering.move_history_renderer for
display — this module implements the inverse conversion.

The Color and Kind characters are carried for sanity-checking/logging only.
Actual move legality is always re-derived from the live board via
RuleEngine (and ownership via SessionManager); neither is ever trusted
from the wire.
"""

from dataclasses import dataclass
from model.position import Position
from model.constants import PieceColor, PieceKind

_COLOR_LETTERS = {"W": PieceColor.WHITE, "B": PieceColor.BLACK}
_MOVE_LENGTH = 6
_JUMP_LENGTH = 5
_JUMP_SUFFIX = "J"
_VALID_FILES = "abcdefgh"


class CommandParseError(ValueError):
    """Raised when a wire command string is malformed or names an invalid square."""


@dataclass(frozen=True)
class MoveCommand:
    """A parsed move command: move the piece at source to destination.

    color/kind are the wire-claimed values, carried for logging/sanity
    checks only — not a source of authorization or legality.
    """
    color: PieceColor
    kind: PieceKind
    source: Position
    destination: Position


@dataclass(frozen=True)
class JumpCommand:
    """A parsed jump command: request a defensive jump for the piece at position.

    color/kind are the wire-claimed values, carried for logging/sanity
    checks only — not a source of authorization or legality.
    """
    color: PieceColor
    kind: PieceKind
    position: Position


class CommandParser:
    """Parses wire command strings into MoveCommand or JumpCommand objects."""

    @staticmethod
    def parse(command: str):
        """Parse a wire command string into a MoveCommand or JumpCommand.

        Dispatches on length and trailing character: a 5-character string
        ending in 'J' is a jump, a 6-character string is a move.

        Raises
        ------
        CommandParseError
            If command has neither recognized shape, or names an invalid
            color, piece kind, or square.
        """
        if len(command) == _JUMP_LENGTH and command.endswith(_JUMP_SUFFIX):
            return CommandParser._parse_jump(command)
        if len(command) == _MOVE_LENGTH:
            return CommandParser._parse_move(command)
        raise CommandParseError(f"Unrecognized command: {command!r}")

    @staticmethod
    def _parse_move(command: str) -> MoveCommand:
        """Parse a 6-character move command."""
        color = CommandParser._parse_color(command[0])
        kind = CommandParser._parse_kind(command[1])
        source = CommandParser._parse_square(command[2:4])
        destination = CommandParser._parse_square(command[4:6])
        return MoveCommand(color=color, kind=kind, source=source, destination=destination)

    @staticmethod
    def _parse_jump(command: str) -> JumpCommand:
        """Parse a 5-character jump command (trailing 'J' already confirmed by caller)."""
        color = CommandParser._parse_color(command[0])
        kind = CommandParser._parse_kind(command[1])
        position = CommandParser._parse_square(command[2:4])
        return JumpCommand(color=color, kind=kind, position=position)

    @staticmethod
    def _parse_color(letter: str) -> PieceColor:
        """Parse a single color letter ('W' or 'B')."""
        if letter not in _COLOR_LETTERS:
            raise CommandParseError(f"Unknown color letter: {letter!r}")
        return _COLOR_LETTERS[letter]

    @staticmethod
    def _parse_kind(letter: str) -> PieceKind:
        """Parse a single piece-kind letter (K, Q, R, B, N, or P)."""
        try:
            return PieceKind(letter)
        except ValueError:
            raise CommandParseError(f"Unknown piece kind letter: {letter!r}")

    @staticmethod
    def _parse_square(square: str) -> Position:
        """Parse a two-character algebraic square (e.g. 'e2') into a Position.

        rank = row + 1 (inverse of MoveHistoryRenderer._pos_to_algebraic),
        so row = rank - 1; file 'a' is column 0.
        """
        if len(square) != 2:
            raise CommandParseError(f"Malformed square: {square!r}")

        file_char, rank_char = square[0], square[1]
        if file_char not in _VALID_FILES or not rank_char.isdigit():
            raise CommandParseError(f"Malformed square: {square!r}")

        col = ord(file_char) - ord("a")
        row = int(rank_char) - 1
        if row < 0:
            raise CommandParseError(f"Square out of range: {square!r}")

        return Position(row, col)
