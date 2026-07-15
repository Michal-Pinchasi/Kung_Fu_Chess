"""
Draws all pieces from a GameSnapshot onto a frame.

Sprite structure expected:
    <pieces_dir>/<KIND><COLOR>/states/<state>/sprites/1.png

Where:
    KIND  = K, Q, R, B, N, P
    COLOR = W (white) or B (black)
    state = idle | move | jump | long_rest | short_rest

The engine uses color "w"/"b" and kind "K"/"Q" etc.
We map: color "w" -> "W", color "b" -> "B".
"""

import os
from typing import Dict, Optional
from graphics.img import Img
from model.game_state import GameSnapshot
from view.ui.layout.layout import Layout
from view.ui.layout.coordinate_mapper import CoordinateMapper
from view.ui.config.ui_config_loader import PIECE_SIZE_FRACTION

_PIECE_SIZE = int(Layout.SQUARE_SIZE * PIECE_SIZE_FRACTION)
_OFFSET = (Layout.SQUARE_SIZE - _PIECE_SIZE) // 2

# Map engine state -> sprite folder name
_STATE_MAP = {
    "idle":    "idle",
    "moving":  "move",
    "jump":    "jump",
    "captured": None,  # do not render captured pieces
}


class PieceRenderer:
    """Loads piece sprites from the asset folder and draws them onto a frame."""

    def __init__(self, pieces_dir: str):
        """
        Parameters
        ----------
        pieces_dir : str
            Path to the folder containing piece subdirectories,
            e.g. view/ui/assets/pieces1
        """
        self._pieces_dir = pieces_dir
        self._cache: Dict[str, Img] = {}

    def _sprite_path(self, kind: str, color: str, state: str) -> Optional[str]:
        """Build the path to sprite frame 1 for the given piece and state."""
        color_letter = "W" if color == "w" else "B"
        folder_name = f"{kind}{color_letter}"   # e.g. "KW", "RB", "PW"
        state_folder = _STATE_MAP.get(state, "idle") or "idle"
        path = os.path.join(
            self._pieces_dir, folder_name, "states", state_folder, "sprites", "1.png"
        )
        return path if os.path.exists(path) else None

    def _load(self, kind: str, color: str, state: str) -> Optional[Img]:
        """Load and cache the sprite for (kind, color, state). Returns None if missing."""
        cache_key = f"{kind}{color}{state}"
        if cache_key not in self._cache:
            path = self._sprite_path(kind, color, state)
            if path is None:
                # fallback to idle
                path = self._sprite_path(kind, color, "idle")
            if path is None:
                self._cache[cache_key] = None
                return None
            self._cache[cache_key] = Img().read(
                path, size=(_PIECE_SIZE, _PIECE_SIZE), keep_aspect=True
            )
        return self._cache[cache_key]

    def draw(self, frame: Img, snapshot: GameSnapshot) -> None:
        """Draw every non-captured piece from snapshot onto frame."""
        for piece in snapshot.pieces:
            if piece.state == "captured":
                continue

            sprite = self._load(piece.kind, piece.color, piece.state)
            if sprite is None:
                continue

            row = int(piece.y)
            col = int(piece.x)
            px, py = CoordinateMapper.cell_to_pixel(row, col)

            # Centre the sprite within the square
            sprite_h, sprite_w = sprite.img.shape[:2]
            cx = px + (Layout.SQUARE_SIZE - sprite_w) // 2
            cy = py + (Layout.SQUARE_SIZE - sprite_h) // 2

            try:
                sprite.draw_on(frame, cx, cy)
            except ValueError:
                # Piece near edge might overflow — skip silently
                pass
