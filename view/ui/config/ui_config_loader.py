"""
Loads UI-specific configuration from ui_config.json.

All rendering classes import from here instead of hard-coding values.
Changing appearance requires editing ui_config.json only.
"""

import json
import os
from typing import Tuple

_path = os.path.join(os.path.dirname(__file__), "ui_config.json")
with open(_path, encoding="utf-8") as _f:
    _c = json.load(_f)

WINDOW_TITLE: str = _c["window_title"]
FPS: int = _c["fps"]

SELECTION_COLOR: Tuple[int, int, int, int] = tuple(_c["selection_color"])
MOVE_HINT_COLOR: Tuple[int, int, int, int] = tuple(_c["move_hint_color"])
GAME_OVER_OVERLAY_COLOR: Tuple[int, int, int, int] = tuple(_c["game_over_overlay_color"])

GAME_OVER_TEXT: str = _c["game_over_text"]
GAME_OVER_FONT_SIZE: float = _c["game_over_font_size"]
GAME_OVER_TEXT_COLOR: Tuple[int, int, int, int] = tuple(_c["game_over_text_color"])
GAME_OVER_TEXT_THICKNESS: int = _c["game_over_text_thickness"]

WINNER_FONT_SIZE: float = _c["winner_font_size"]
WINNER_TEXT_COLOR: Tuple[int, int, int, int] = tuple(_c["winner_text_color"])
WINNER_TEXT_THICKNESS: int = _c["winner_text_thickness"]

PIECE_SIZE_FRACTION: float = _c["piece_size_fraction"]
SPRITE_FRAME_DURATION_MS: int = _c["sprite_frame_duration_ms"]
SPRITE_FRAME_COUNT: int = _c["sprite_frame_count"]
