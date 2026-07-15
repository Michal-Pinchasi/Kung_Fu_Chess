"""
Draws UI overlays onto a frame exclusively through the Img API.

No direct cv2 calls — all drawing goes through Img.draw_rect() and Img.put_text().
"""

from graphics.img import Img
from model.game_state import GameSnapshot
from view.ui.layout.layout import Layout
from view.ui.layout.coordinate_mapper import CoordinateMapper
from view.ui.config.ui_config_loader import (
    SELECTION_COLOR,
    GAME_OVER_OVERLAY_COLOR,
    GAME_OVER_TEXT,
    GAME_OVER_FONT_SIZE,
    GAME_OVER_TEXT_COLOR,
    GAME_OVER_TEXT_THICKNESS,
    WINNER_FONT_SIZE,
    WINNER_TEXT_COLOR,
    WINNER_TEXT_THICKNESS,
)


class OverlayRenderer:
    """Draws selection highlights and game-over overlays using only Img methods."""

    def draw(self, frame: Img, snapshot: GameSnapshot) -> None:
        """Apply all overlays relevant to the current snapshot."""
        self._draw_selection(frame, snapshot)
        if snapshot.game_over:
            self._draw_game_over(frame, snapshot)

    def _draw_selection(self, frame: Img, snapshot: GameSnapshot) -> None:
        """Draw a semi-transparent highlight on the selected cell via Img.draw_rect."""
        if snapshot.selected_cell is None:
            return
        row = snapshot.selected_cell.row
        col = snapshot.selected_cell.col
        px, py = CoordinateMapper.cell_to_pixel(row, col)
        s = Layout.SQUARE_SIZE
        alpha = SELECTION_COLOR[3] / 255.0
        color_bgr = (SELECTION_COLOR[2], SELECTION_COLOR[1], SELECTION_COLOR[0], 255)

        # Filled semi-transparent rectangle
        frame.draw_rect(px, py, s, s, color=color_bgr, thickness=-1, alpha=alpha)
        # Solid border
        frame.draw_rect(px, py, s, s, color=color_bgr, thickness=3, alpha=1.0)

    def _draw_game_over(self, frame: Img, snapshot: GameSnapshot) -> None:
        """Darken the board and draw game-over text via Img methods."""
        bx, by = Layout.BOARD_X, Layout.BOARD_Y
        bs = Layout.BOARD_SIZE
        alpha = GAME_OVER_OVERLAY_COLOR[3] / 255.0
        overlay_color = (
            GAME_OVER_OVERLAY_COLOR[2],
            GAME_OVER_OVERLAY_COLOR[1],
            GAME_OVER_OVERLAY_COLOR[0],
            255,
        )

        # Dark semi-transparent board overlay
        frame.draw_rect(bx, by, bs, bs, color=overlay_color, thickness=-1, alpha=alpha)

        # "GAME OVER" centred on the board
        cx = bx + bs // 2 - 180
        cy = by + bs // 2
        frame.put_text(
            GAME_OVER_TEXT, cx, cy,
            GAME_OVER_FONT_SIZE,
            color=tuple(GAME_OVER_TEXT_COLOR),
            thickness=GAME_OVER_TEXT_THICKNESS,
        )

        # Winner text
        winner = getattr(snapshot, "winner", None)
        if winner:
            frame.put_text(
                f"{winner} WINS", cx + 30, cy + 70,
                WINNER_FONT_SIZE,
                color=tuple(WINNER_TEXT_COLOR),
                thickness=WINNER_TEXT_THICKNESS,
            )
