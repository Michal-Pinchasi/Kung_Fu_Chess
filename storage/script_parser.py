class ScriptParser:
    """Splits a full Kung Fu Chess text script into its two sections.

    Script format:
        Board:
        <board rows>
        Commands:
        <command lines>

    Does not itself parse the board grid or the command lines — that is
    BoardParser's and Controller's job respectively. This class only knows
    about the "Board:"/"Commands:" envelope.
    """

    @staticmethod
    def split(input_text: str) -> tuple[str, list[str]]:
        """Return (board_text, command_lines).

        Lines before "Commands:" belong to the board section; lines after
        belong to the command section. The "Board:"/"Commands:" marker lines
        themselves and blank lines are dropped.
        """
        lines = input_text.strip().split("\n")
        board_lines = []
        command_lines = []

        in_commands = False
        for line in lines:
            cleaned_line = line.strip()
            if not cleaned_line:
                continue
            if cleaned_line.startswith("Commands:"):
                in_commands = True
                continue
            if cleaned_line.startswith("Board:"):
                continue
            if not in_commands:
                board_lines.append(cleaned_line)
            else:
                command_lines.append(cleaned_line)

        return "\n".join(board_lines), command_lines
