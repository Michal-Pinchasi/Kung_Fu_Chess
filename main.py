import sys
from storage.script_parser import ScriptParser
from storage.board_parser import (
    BoardParser, BoardParseError, RowWidthMismatchError, UnknownPieceTokenError,
)
from engin.game_engine import GameEngine
from config.config_loader import ERR_UNKNOWN_TOKEN, ERR_ROW_WIDTH_MISMATCH


def run_game_from_text(input_text: str) -> None:
    """Parse a text script and run it against a fresh engine.

    Prints a stable error token to stdout when board parsing fails.
    """
    board_text, command_lines = ScriptParser.split(input_text)

    try:
        board = BoardParser.parse(board_text)
    except RowWidthMismatchError:
        print(ERR_ROW_WIDTH_MISMATCH)
        return
    except UnknownPieceTokenError:
        print(ERR_UNKNOWN_TOKEN)
        return
    except BoardParseError:
        print("ERROR")
        return

    engine = GameEngine(board)
    engine.controller.run_script(command_lines)


def main() -> None:
    """Entry point: read a full script from stdin and run it."""
    input_data = sys.stdin.read()
    if input_data.strip():
        run_game_from_text(input_data)


if __name__ == "__main__":
    main()
