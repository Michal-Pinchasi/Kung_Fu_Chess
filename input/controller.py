from model.position import Position
from input.board_mapper import BoardMapper


class Controller:
    """Translates user input into game commands.

    Maintains selected-cell state and applies the two-click selection
    protocol. Does not decide chess legality and does not mutate Board directly.
    """

    def __init__(self, game_engine):
        self.engine = game_engine
        self.board = game_engine.board
        self.selected_cell = None

    def click(self, x: int, y: int) -> None:
        """Convert pixel coordinates to a cell and handle the click."""
        pos = BoardMapper.pixel_to_cell(x, y, self.board.width, self.board.height)
        if pos is not None:
            self.handle_click(pos)

    def handle_click(self, position: Position) -> None:
        """Process a click on a board cell using the two-click selection protocol.

        First click: select the piece at position (ignored when cell is empty).
        Second click on friendly piece: re-select that piece instead.
        Second click elsewhere: request a move from selected cell to position.
        Selection is cleared after every second in-board click.
        """
        if self.engine.game_state.is_game_over:
            return

        piece = self.board.get_piece(position.row, position.col)

        if self.selected_cell is None:
            if piece != "." and piece is not None:
                self.selected_cell = position
            return

        src = self.selected_cell
        self.selected_cell = None

        if piece != "." and piece is not None:
            src_piece = self.board.get_piece(src.row, src.col)
            if src_piece != "." and src_piece is not None and piece.color == src_piece.color:
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
                    int(parts[1]), int(parts[2]), self.board.width, self.board.height
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
