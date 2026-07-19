from model.position import Position
from input.board_mapper import BoardMapper
from view.ui.layout.coordinate_mapper import CoordinateMapper
from storage.board_printer import BoardPrinter


class Controller:
    """Translates user input into game commands.

    Maintains selected-cell state and applies the two-click selection
    protocol. Does not read the board directly, does not evaluate piece
    colors or emptiness, and does not check game_over. All game-state
    queries go through GameEngine.

    Owns all pixel-to-cell translation for both entry points: the flat
    CELL_SIZE-based BoardMapper for the headless text-script protocol
    (click/execute_command), and the window-layout-aware CoordinateMapper
    for real GUI mouse events (handle_pixel_click/handle_pixel_jump). This
    keeps GameEngine itself completely unaware of pixels or screen layout.
    """

    def __init__(self, game_engine):
        self.engine = game_engine
        self.selected_cell = None

    def handle_pixel_click(self, px: int, py: int) -> None:
        """Translate a real window pixel click into a board cell and apply
        the two-click selection protocol. Clears the current selection when
        the click falls outside the board.
        """
        result = CoordinateMapper.pixel_to_cell(px, py)
        if result is None:
            self.selected_cell = None
            return
        row, col = result
        self.handle_click(Position(row, col))

    def handle_pixel_jump(self, px: int, py: int) -> None:
        """Translate a real window pixel right-click into a board cell and
        request a defensive jump there. Ignored when the click falls outside
        the board.
        """
        result = CoordinateMapper.pixel_to_cell(px, py)
        if result is None:
            return
        row, col = result
        self.engine.request_jump(Position(row, col))

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

    def run_script(self, command_lines: list) -> None:
        """Execute a full script's worth of command lines in order.

        "print board" is handled directly (a reporting concern, not a game
        action); every other command (click, jump, wait) is delegated to
        execute_command, which already implements the full command protocol.
        """
        for cmd in command_lines:
            parts = cmd.strip().split()
            if not parts:
                continue

            if parts[0].lower() == "print" and len(parts) > 1 and parts[1].lower() == "board":
                print(BoardPrinter.print_board(self.engine.board))
            else:
                self.execute_command(cmd)
