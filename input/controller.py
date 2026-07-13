from model.position import Position
from input.board_mapper import BoardMapper


class Controller:
    """Translates user input into game commands.

    Maintains selected-cell state and applies the two-click selection
    protocol. Does not read the board directly, does not evaluate piece
    colors or emptiness, and does not check game_over. All game-state
    queries go through GameEngine.
    """

    def __init__(self, game_engine):
        self.engine = game_engine
        self.selected_cell = None

    def click(self, x: int, y: int) -> None:
        """Convert pixel coordinates to a board cell and handle the click.

        Out-of-bounds clicks are ignored when no piece is selected.
        Out-of-bounds clicks clear selection when a piece is already selected.
        """
        pos = BoardMapper.pixel_to_cell(
            x, y, self.engine.board.width, self.engine.board.height
        )
        if pos is None:
            if self.selected_cell is not None:
                self.selected_cell = None
            return
        self.handle_click(pos)

    def handle_click(self, position: Position) -> None:
        """Process an in-bounds click using the two-click selection protocol.

        First click: select the cell when it contains a piece (via engine query).
        Second click on friendly piece: switch selection to the new piece.
        Second click elsewhere: send request_move to the engine and clear selection.
        Selection is always cleared after the second in-bounds click.
        """
        if self.selected_cell is None:
            if not self.engine.is_cell_empty(position):
                self.selected_cell = position
            return

        src = self.selected_cell
        self.selected_cell = None

        if self.engine.is_friendly_piece(position, src):
            self.selected_cell = position
            return

        if src != position:
            self.engine.request_move(src, position)

    def execute_command(self, command_str: str) -> None:
        """Parse and dispatch a raw command string (click, jump, or wait)."""
        parts = command_str.strip().split()
        if not parts:
            return

        cmd_type = parts[0].lower()

        if cmd_type == "click":
            try:
                self.click(int(parts[1]), int(parts[2]))
            except (IndexError, ValueError):
                pass

        elif cmd_type == "jump":
            try:
                pos = BoardMapper.pixel_to_cell(
                    int(parts[1]), int(parts[2]),
                    self.engine.board.width, self.engine.board.height,
                )
                if pos is not None:
                    self.engine.request_jump(pos)
            except (IndexError, ValueError):
                pass

        elif cmd_type == "wait":
            try:
                self.engine.wait(int(parts[1]))
            except (IndexError, ValueError):
                pass
