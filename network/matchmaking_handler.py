"""Authenticated matchmaking queue action handling."""

import logging


class MatchmakingHandler:
    """Handles joining and leaving the automatic opponent queue."""

    def __init__(
        self, matchmaking, rooms, settings, lifecycle, sender, logger, event_writer
    ):
        self._matchmaking = matchmaking
        self._rooms = rooms
        self._settings = settings
        self._lifecycle = lifecycle
        self._sender = sender
        self._logger = logger
        self._write_event = event_writer

    async def handle(self, websocket, user, action) -> bool:
        if action == "join_queue":
            await self.join(websocket, user)
            return True
        if action == "leave_queue":
            await self.leave(websocket, user)
            return True
        return False

    async def join(self, websocket, user) -> None:
        if self._rooms.for_user(user.id):
            await self._sender.send(
                websocket,
                {"type": "matchmaking_error", "reason": "already_in_game"},
            )
            return
        try:
            self._matchmaking.join(user, websocket)
        except ValueError as error:
            await self._sender.send(
                websocket, {"type": "matchmaking_error", "reason": str(error)}
            )
            return
        await self._sender.send(
            websocket,
            {
                "type": "queue_joined",
                "timeout_seconds": self._settings.matchmaking.queue_timeout_seconds,
            },
        )
        self._write_event(
            self._logger,
            logging.INFO,
            "queue_joined",
            user_id=user.id,
            rating=user.rating,
        )
        await self._lifecycle.create_available_matches()

    async def leave(self, websocket, user) -> None:
        removed = self._matchmaking.leave(user.id)
        await self._sender.send(
            websocket, {"type": "queue_left", "was_queued": removed is not None}
        )
