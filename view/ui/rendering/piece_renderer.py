"""
Draws all pieces from a GameSnapshot onto a frame.

Sprite structure expected:
    <pieces_dir>/<KIND><COLOR>/states/<state>/sprites/<frame>.png
    where <frame> is 1..5

Where:
    KIND  = K, Q, R, B, N, P
    COLOR = W (white) or B (black)
    state = idle | move | jump | long_rest | short_rest

The engine uses color "w"/"b" and kind "K"/"Q" etc.
We map: color "w" -> "W", color "b" -> "B".

While a piece is "moving" or "jump", its 5-frame sprite set is cycled at a
fixed pace (SPRITE_FRAME_DURATION_MS per frame) based on how long it has
been in that state, so it visibly walks/jumps rather than gliding with a
static pose. Idle pieces always show frame 1.
"""

import os
from typing import Dict, Optional
from graphics.img import Img
from model.game_state import GameSnapshot
from view.ui.layout.layout import Layout
from view.ui.layout.coordinate_mapper import CoordinateMapper
from view.ui.config.ui_config_loader import (
    PIECE_SIZE_FRACTION, SPRITE_FRAME_DURATION_MS, SPRITE_FRAME_COUNT,
)

_PIECE_SIZE = int(Layout.SQUARE_SIZE * PIECE_SIZE_FRACTION)
_OFFSET = (Layout.SQUARE_SIZE - _PIECE_SIZE) // 2
_ANIMATED_STATES = {"moving", "jump"}

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

    def _sprite_path(self, kind: str, color: str, state: str, frame: int) -> Optional[str]:
        """Build the path to the given sprite frame for the given piece and state."""
        color_letter = "W" if color == "w" else "B"
        folder_name = f"{kind}{color_letter}"   # e.g. "KW", "RB", "PW"
        state_folder = _STATE_MAP.get(state, "idle") or "idle"
        path = os.path.join(
            self._pieces_dir, folder_name, "states", state_folder, "sprites", f"{frame}.png"
        )
        return path if os.path.exists(path) else None

    def _load(self, kind: str, color: str, state: str, frame: int) -> Optional[Img]:
        """Load and cache the sprite for (kind, color, state, frame). Returns None if missing."""
        cache_key = f"{kind}{color}{state}{frame}"
        if cache_key not in self._cache:
            path = self._sprite_path(kind, color, state, frame)
            if path is None:
                # fallback to frame 1 of the same state
                path = self._sprite_path(kind, color, state, 1)
            if path is None:
                # fallback to idle frame 1
                path = self._sprite_path(kind, color, "idle", 1)
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

            sprite_frame = 1
            if piece.state in _ANIMATED_STATES:
                sprite_frame = (piece.elapsed_state_ms // SPRITE_FRAME_DURATION_MS) % SPRITE_FRAME_COUNT + 1

            sprite = self._load(piece.kind, piece.color, piece.state, sprite_frame)
            if sprite is None:
                continue

            px, py = CoordinateMapper.cell_to_pixel_f(piece.y, piece.x)

            # Centre the sprite within the square
            sprite_h, sprite_w = sprite.img.shape[:2]
            cx = int(px) + (Layout.SQUARE_SIZE - sprite_w) // 2
            cy = int(py) + (Layout.SQUARE_SIZE - sprite_h) // 2

            try:
                sprite.draw_on(frame, cx, cy)
            except ValueError:
                # Piece near edge might overflow — skip silently
                pass
