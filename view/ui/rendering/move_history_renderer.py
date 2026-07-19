"""
Renders the move history panels on both sides of the board.

Left panel: white moves
Right panel: black moves

Each panel also shows the player's accumulated capture score, drawn
prominently near the bottom via _draw_score().
"""

from view.ui.graphics.img import Img
from model.game_state import GameSnapshot
from view.ui.layout.layout import Layout


class MoveHistoryRenderer:
    """Displays move history and score for both players in side panels."""

    def __init__(self):
        pass

    def draw(self, frame: Img, snapshot: GameSnapshot) -> None:
        """Draw move history and score panels for white (left) and black (right)."""
        if snapshot.move_history is not None:
            self._draw_panel(
                frame,
                snapshot.move_history.get_white_moves(),
                Layout.WHITE_PANEL_X,
                Layout.WHITE_PANEL_Y,
                "White"
            )
            self._draw_panel(
                frame,
                snapshot.move_history.get_black_moves(),
                Layout.BLACK_PANEL_X,
                Layout.BLACK_PANEL_Y,
                "Black"
            )

        if snapshot.score is not None:
            self._draw_score(frame, Layout.WHITE_PANEL_X, Layout.WHITE_PANEL_Y, snapshot.score.white_score)
            self._draw_score(frame, Layout.BLACK_PANEL_X, Layout.BLACK_PANEL_Y, snapshot.score.black_score)

    def _draw_panel(self, frame: Img, moves: list, x: int, y: int, player_name: str) -> None:
        """Draw a single move history panel."""
        # Draw background rectangle
        frame.draw_rect(
            x, y,
            Layout.MOVE_PANEL_WIDTH, Layout.MOVE_PANEL_HEIGHT,
            color=Layout.PANEL_BACKGROUND_COLOR,
            thickness=-1,
            alpha=Layout.PANEL_BACKGROUND_ALPHA
        )

        # Draw border
        frame.draw_rect(
            x, y,
            Layout.MOVE_PANEL_WIDTH, Layout.MOVE_PANEL_HEIGHT,
            color=Layout.PANEL_BORDER_COLOR,
            thickness=Layout.PANEL_BORDER_THICKNESS
        )

        # Draw player name title
        frame.put_text(
            player_name,
            x + Layout.MOVE_TEXT_X_OFFSET,
            y + Layout.MOVE_TITLE_Y_OFFSET,
            font_size=Layout.MOVE_TITLE_FONT_SIZE,
            color=Layout.MOVE_TEXT_COLOR,
            thickness=Layout.MOVE_TEXT_THICKNESS
        )

        # Draw separator line
        frame.draw_rect(
            x + Layout.PANEL_SEPARATOR_MARGIN, y + Layout.MOVE_SEPARATOR_Y_OFFSET,
            Layout.MOVE_PANEL_WIDTH - 2 * Layout.PANEL_SEPARATOR_MARGIN, Layout.SEPARATOR_LINE_HEIGHT,
            color=Layout.PANEL_BORDER_COLOR,
            thickness=Layout.SEPARATOR_LINE_HEIGHT
        )

        # Draw moves — leave room at the bottom for the score line
        moves_bottom = y + Layout.MOVE_PANEL_HEIGHT - Layout.SCORE_BOTTOM_MARGIN - Layout.SCORE_SEPARATOR_GAP
        current_y = y + Layout.MOVE_TEXT_Y_OFFSET + 5
        for i, move in enumerate(moves):
            if current_y + Layout.MOVE_TEXT_LINE_HEIGHT > moves_bottom:
                # Reached the space reserved for the score line, stop drawing
                frame.put_text(
                    "...",
                    x + Layout.MOVE_TEXT_X_OFFSET,
                    current_y,
                    font_size=Layout.MOVE_FONT_SIZE,
                    color=Layout.MOVE_TEXT_COLOR,
                    thickness=Layout.MOVE_TEXT_THICKNESS
                )
                break

            # Format move string: "P a2-a4" or "N c3xd5" (with capture indicator)
            source_str = self._pos_to_algebraic(move.source)
            dest_str = self._pos_to_algebraic(move.destination)
            capture_indicator = "x" if move.is_capture else "-"
            move_str = f"{i + 1}. {move.piece_kind} {source_str}{capture_indicator}{dest_str}"

            frame.put_text(
                move_str,
                x + Layout.MOVE_TEXT_X_OFFSET,
                current_y,
                font_size=Layout.MOVE_FONT_SIZE,
                color=Layout.MOVE_TEXT_COLOR,
                thickness=Layout.MOVE_TEXT_THICKNESS
            )

            current_y += Layout.MOVE_TEXT_LINE_HEIGHT

    def _draw_score(self, frame: Img, x: int, y: int, score: int) -> None:
        """Draw the accumulated score prominently near the bottom of a panel."""
        score_y = y + Layout.MOVE_PANEL_HEIGHT - Layout.SCORE_BOTTOM_MARGIN

        frame.draw_rect(
            x + Layout.PANEL_SEPARATOR_MARGIN, score_y - Layout.SCORE_SEPARATOR_GAP,
            Layout.MOVE_PANEL_WIDTH - 2 * Layout.PANEL_SEPARATOR_MARGIN, Layout.SEPARATOR_LINE_HEIGHT,
            color=Layout.PANEL_BORDER_COLOR,
            thickness=Layout.SEPARATOR_LINE_HEIGHT
        )

        frame.put_text(
            f"Score: {score}",
            x + Layout.MOVE_TEXT_X_OFFSET,
            score_y,
            font_size=Layout.SCORE_FONT_SIZE,
            color=Layout.SCORE_TEXT_COLOR,
            thickness=Layout.SCORE_TEXT_THICKNESS
        )

    def _pos_to_algebraic(self, pos) -> str:
        """Convert Position to algebraic notation (e.g., 'a2').

        White occupies rows 0-1 (rank 1-2) and black rows 6-7 (rank 7-8)
        on this board, so rank number = row + 1.
        """
        col_letter = chr(ord('a') + pos.col)
        row_number = pos.row + 1
        return f"{col_letter}{row_number}"
