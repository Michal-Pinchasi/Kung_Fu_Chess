"""Rating-aware matchmaking queue with deterministic timeout handling."""

from dataclasses import dataclass
import bisect
import time


@dataclass(frozen=True)
class QueuedPlayer:
    user: object
    websocket: object
    rating: int
    joined_at: float


class MatchmakingManager:
    """Owns queue ordering and pairing; performs no network I/O."""

    def __init__(self, elo_range: int, timeout_seconds: float, clock=time.monotonic):
        self.elo_range = elo_range
        self.timeout_seconds = timeout_seconds
        self._clock = clock
        self._players: list[QueuedPlayer] = []

    def join(self, user, websocket) -> QueuedPlayer:
        if self.contains(user.id):
            raise ValueError("already_in_queue")
        entry = QueuedPlayer(user, websocket, user.rating, self._clock())
        keys = [(player.rating, player.joined_at) for player in self._players]
        index = bisect.bisect_right(keys, (entry.rating, entry.joined_at))
        self._players.insert(index, entry)
        return entry

    def leave(self, user_id: int) -> QueuedPlayer | None:
        for index, player in enumerate(self._players):
            if player.user.id == user_id:
                return self._players.pop(index)
        return None

    def remove_connection(self, websocket) -> QueuedPlayer | None:
        for player in tuple(self._players):
            if player.websocket is websocket:
                return self.leave(player.user.id)
        return None

    def contains(self, user_id: int) -> bool:
        return any(player.user.id == user_id for player in self._players)

    def find_matches(self) -> list[tuple[QueuedPlayer, QueuedPlayer]]:
        matches = []
        available = sorted(self._players, key=lambda player: player.joined_at)
        matched_ids = set()
        for player in available:
            if player.user.id in matched_ids:
                continue
            candidates = [candidate for candidate in available
                          if candidate.user.id not in matched_ids
                          and candidate.user.id != player.user.id
                          and abs(candidate.rating - player.rating) <= self.elo_range]
            if not candidates:
                continue
            opponent = min(candidates, key=lambda candidate: (abs(candidate.rating - player.rating), candidate.joined_at))
            matched_ids.update((player.user.id, opponent.user.id))
            matches.append((player, opponent))
        if matched_ids:
            self._players = [player for player in self._players if player.user.id not in matched_ids]
        return matches

    def expired(self) -> list[QueuedPlayer]:
        now = self._clock()
        expired = [player for player in self._players if now - player.joined_at >= self.timeout_seconds]
        expired_ids = {player.user.id for player in expired}
        self._players = [player for player in self._players if player.user.id not in expired_ids]
        return expired

    def __len__(self) -> int:
        return len(self._players)
