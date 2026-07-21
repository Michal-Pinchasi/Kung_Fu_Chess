"""Connects domain game events to structured audit logging."""

import logging

from events.game_events import (GAME_OVER, JUMP_STARTED, MOVE_COMPLETED,
                                MOVE_STARTED, SCORE_CHANGED)


class GameEventAuditor:
    EVENT_TYPES = (MOVE_STARTED, JUMP_STARTED, MOVE_COMPLETED, SCORE_CHANGED, GAME_OVER)

    def __init__(self, logger, event_writer):
        self.logger = logger
        self.event_writer = event_writer

    def attach(self, bus, game_id: str) -> None:
        for event_type in self.EVENT_TYPES:
            bus.subscribe(event_type, self._handler(game_id, event_type))

    def _handler(self, game_id, event_type):
        def audit(payload):
            details = vars(payload) if hasattr(payload, "__dict__") else {"payload": payload}
            self.event_writer(self.logger, logging.INFO, "game_event",
                              game_id=game_id, event_type=event_type, details=details)
        return audit
