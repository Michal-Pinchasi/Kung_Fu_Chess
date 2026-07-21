import pytest
from model.position import Position
from model.constants import PieceColor, PieceKind
from network.command_parser import CommandParser, CommandParseError, MoveCommand, JumpCommand


def test_parse_valid_move_command():
    command = CommandParser.parse("WQe2e5")

    assert isinstance(command, MoveCommand)
    assert command.color == PieceColor.WHITE
    assert command.kind == PieceKind.QUEEN
    assert command.source == Position(1, 4)       # e2 -> row 1, col 4
    assert command.destination == Position(4, 4)   # e5 -> row 4, col 4


def test_parse_valid_move_command_black():
    command = CommandParser.parse("BPa7a5")

    assert command.color == PieceColor.BLACK
    assert command.kind == PieceKind.PAWN
    assert command.source == Position(6, 0)
    assert command.destination == Position(4, 0)


def test_parse_valid_jump_command():
    command = CommandParser.parse("WKe1J")

    assert isinstance(command, JumpCommand)
    assert command.color == PieceColor.WHITE
    assert command.kind == PieceKind.KING
    assert command.position == Position(0, 4)


@pytest.mark.parametrize("bad_command", [
    "",
    "WQe2",           # too short for a move, too short for a jump
    "WQe2e5x",        # 7 chars, not a recognized length
    "WQe2e",           # 5 chars but doesn't end in J
])
def test_parse_unrecognized_length_raises(bad_command):
    with pytest.raises(CommandParseError):
        CommandParser.parse(bad_command)


def test_parse_unknown_color_letter_raises():
    with pytest.raises(CommandParseError):
        CommandParser.parse("XQe2e5")


def test_parse_unknown_kind_letter_raises():
    with pytest.raises(CommandParseError):
        CommandParser.parse("WXe2e5")


@pytest.mark.parametrize("bad_square_command", [
    "WQz2e5",   # invalid file
    "WQe0e5",   # rank must be >= 1
    "WQeZe5",   # non-digit rank
])
def test_parse_invalid_square_raises(bad_square_command):
    with pytest.raises(CommandParseError):
        CommandParser.parse(bad_square_command)
