from storage.script_parser import ScriptParser


def test_split_well_formed_script():
    script = (
        "Board:\n"
        "wK . .\n"
        ". . bK\n"
        "Commands:\n"
        "click 100 100\n"
        "wait 1000\n"
    )
    board_text, command_lines = ScriptParser.split(script)

    assert board_text == "wK . .\n. . bK"
    assert command_lines == ["click 100 100", "wait 1000"]


def test_split_ignores_blank_lines():
    script = (
        "Board:\n"
        "\n"
        "wK . .\n"
        "\n"
        "Commands:\n"
        "\n"
        "wait 500\n"
        "\n"
    )
    board_text, command_lines = ScriptParser.split(script)

    assert board_text == "wK . ."
    assert command_lines == ["wait 500"]


def test_split_with_no_commands_section():
    script = (
        "Board:\n"
        "wK . .\n"
    )
    board_text, command_lines = ScriptParser.split(script)

    assert board_text == "wK . ."
    assert command_lines == []


def test_split_with_no_board_marker():
    """Lines before 'Commands:' are treated as board text even without a 'Board:' marker."""
    script = (
        "wK . .\n"
        "Commands:\n"
        "wait 100\n"
    )
    board_text, command_lines = ScriptParser.split(script)

    assert board_text == "wK . ."
    assert command_lines == ["wait 100"]
