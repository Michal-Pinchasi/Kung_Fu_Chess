"""Tracks reconnect grace periods without knowing WebSockets or game rules."""

from dataclasses import dataclass
import math
import time


@dataclass
class DisconnectState:
    game_id: str
    user_id: int
    deadline: float
    last_reported: int | None = None


class DisconnectManager:
    def __init__(self, grace_seconds: float, clock=time.monotonic):
        if not 20 <= grace_seconds <= 30:
            raise ValueError("disconnect grace period must be between 20 and 30 seconds")
        self.grace_seconds = grace_seconds
        self._clock = clock
        self._states: dict[tuple[str, int], DisconnectState] = {}

    def start(self, game_id: str, user_id: int) -> DisconnectState:
        state = DisconnectState(game_id, user_id, self._clock() + self.grace_seconds)
        self._states[(game_id, user_id)] = state
        return state

    def cancel(self, game_id: str, user_id: int) -> bool:
        state = self._states.pop((game_id, user_id), None)
        return state is not None and state.deadline > self._clock()

    def contains(self, game_id: str, user_id: int) -> bool:
        return (game_id, user_id) in self._states

    def cancel_game(self, game_id: str) -> None:
        keys = [key for key in self._states if key[0] == game_id]
        for key in keys:
            self._states.pop(key, None)

    def updates(self) -> list[tuple[DisconnectState, int]]:
        now = self._clock()
        updates = []
        for state in self._states.values():
            remaining = max(0, math.ceil(state.deadline - now))
            if remaining != state.last_reported:
                state.last_reported = remaining
                updates.append((state, remaining))
        return updates

    def expired(self) -> list[DisconnectState]:
        now = self._clock()
        expired = [state for state in self._states.values() if state.deadline <= now]
        for state in expired:
            self._states.pop((state.game_id, state.user_id), None)
        return expired
