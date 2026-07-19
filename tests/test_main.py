from main import run_game_from_text
from config.config_loader import ERR_UNKNOWN_TOKEN, ERR_ROW_WIDTH_MISMATCH

_EMPTY_8X8_WITH_ROOK = (
    "wR . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
    ". . . . . . . .\n"
)


def test_run_executes_valid_script_and_prints_board(capsys):
    script = (
        "Board:\n"
        "wK . .\n"
        ". . bK\n"
        "Commands:\n"
        "print board\n"
    )
    run_game_from_text(script)

    captured = capsys.readouterr()
    assert "wK" in captured.out
    assert "bK" in captured.out


def test_run_executes_click_and_wait_commands(capsys):
    """A full click+click+wait+print script actually moves the piece."""
    script = "Board:\n" + _EMPTY_8X8_WITH_ROOK + "Commands:\nclick 50 50\nclick 550 50\nwait 5000\nprint board\n"

    run_game_from_text(script)

    captured = capsys.readouterr()
    first_row = captured.out.strip().split("\n")[0].split()
    assert first_row[0] == "."
    assert first_row[5] == "wR"


def test_run_row_width_mismatch_prints_stable_error_token(capsys):
    script = "Board:\nwK . .\n. bK\nCommands:\n"

    run_game_from_text(script)

    captured = capsys.readouterr()
    assert captured.out.strip() == ERR_ROW_WIDTH_MISMATCH


def test_run_unknown_token_prints_stable_error_token(capsys):
    script = "Board:\nwK . wX\nCommands:\n"

    run_game_from_text(script)

    captured = capsys.readouterr()
    assert captured.out.strip() == ERR_UNKNOWN_TOKEN


def test_run_empty_board_prints_generic_error(capsys):
    script = "Board:\nCommands:\nprint board\n"

    run_game_from_text(script)

    captured = capsys.readouterr()
    assert captured.out.strip() == "ERROR"
