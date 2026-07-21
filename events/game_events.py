"""
Event-type constants and payload dataclasses published by GameEngine on its
injected MessageBus.

Every event type string here corresponds to exactly one payload dataclass.
Consumers (subscribers) can rely on receiving that exact type as the
payload argument to their handler.
"""

from dataclasses import dataclass
from typing import Optional
from model.position import Position

MOVE_STARTED = "move_started"
JUMP_STARTED = "jump_started"
MOVE_COMPLETED = "move_completed"
SCORE_CHANGED = "score_changed"
GAME_OVER = "game_over"


@dataclass(frozen=True)
class MoveStartedEvent:
    """Published when a move request is accepted and scheduled, before it lands."""
    piece_id: str
    kind: str
    color: str
    source: Position
    destination: Position


@dataclass(frozen=True)
class JumpStartedEvent:
    """Published when a defensive jump request is accepted and scheduled."""
    piece_id: str
    kind: str
    color: str
    position: Position


@dataclass(frozen=True)
class MoveCompletedEvent:
    """Published when a previously-started move lands on its destination."""
    piece_id: str
    kind: str
    color: str
    source: Position
    destination: Position
    is_capture: bool


@dataclass(frozen=True)
class ScoreChangedEvent:
    """Published whenever either side's accumulated capture score changes."""
    white_score: int
    black_score: int


@dataclass(frozen=True)
class GameOverEvent:
    """Published once, when a king capture ends the game."""
    winner: Optional[str]
