"""
Loads project-wide constants from constants.json.

All other modules import directly from this file, remaining unaware
of the underlying JSON source.
"""

import json
import os

def _load() -> dict:
    path = os.path.join(os.path.dirname(__file__), "constants.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

_c = _load()

CELL_SIZE: int                    = _c["CELL_SIZE"]
MILLISECONDS_PER_CELL: int        = _c["MILLISECONDS_PER_CELL"]
JUMP_DURATION_MILLISECONDS: int   = _c["JUMP_DURATION_MILLISECONDS"]
LONG_REST_DURATION_MILLISECONDS: int  = _c["LONG_REST_DURATION_MILLISECONDS"]
SHORT_REST_DURATION_MILLISECONDS: int = _c["SHORT_REST_DURATION_MILLISECONDS"]
TIME_STEP_MS: int                 = _c["TIME_STEP_MS"]
PIECE_VALUES: dict                = _c["PIECE_VALUES"]
EMPTY_SQUARE: str                 = _c["EMPTY_SQUARE"]
ERR_UNKNOWN_TOKEN: str            = _c["ERR_UNKNOWN_TOKEN"]
ERR_ROW_WIDTH_MISMATCH: str       = _c["ERR_ROW_WIDTH_MISMATCH"]
