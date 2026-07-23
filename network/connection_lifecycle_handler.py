"""In-game disconnection countdown and technical-forfeit handling."""

import logging


class ConnectionLifecycleHandler:
    """Tracks temporary game disconnects and delegates expired results."""

    def __init__(
        self,
        games,
        rooms,
        disconnects,
        grace_period_seconds,
        result_coordinator,
        sender,
        logger,
        event_writer,
    ):
        self._games = games
        self._rooms = rooms
        self._disconnects = disconnects
        self._grace_period_seconds = grace_period_seconds
        self._results = result_coordinator
        self._sender = sender
        self._logger = logger
        self._write_event = event_writer

    async def disconnect(self, user) -> None:
        room = self._rooms.for_user(user.id)
        if room is None:
            return
        member = room.disconnect(user.id)
        game = self._games.get(room.game_id) if room.game_id else None
        if game and not game.finished and member.role.can_play:
            game.disconnect(user.id)
            self._disconnects.start(game.game_id, user.id)
            await self._notify(
                room, user.id, user.username, int(self._grace_period_seconds)
            )
        self._write_event(
            self._logger,
            logging.INFO,
            "room_member_disconnected",
            room_id=room.room_id,
            user_id=user.id,
            role=member.role.value,
        )

    async def process(self) -> None:
        for state, remaining in self._disconnects.updates():
            game = self._games.get(state.game_id)
            if game and not game.finished:
                disconnected = game.slot_for_user(state.user_id)
                await self._notify(
                    self._rooms.for_game(game.game_id),
                    state.user_id,
                    disconnected.user.username,
                    remaining,
                )
        for state in self._disconnects.expired():
            game = self._games.get(state.game_id)
            if game and not game.finished:
                winner = game.opponent_of(state.user_id)
                await self._results.finish(
                    game, winner.user.id, "technical_forfeit"
                )

    async def _notify(
        self, room, disconnected_user_id, username, remaining_seconds
    ) -> None:
        await self._sender.broadcast_room(
            room,
            {
                "type": "opponent_disconnected",
                "username": username,
                "remaining_seconds": remaining_seconds,
            },
            exclude_user_id=disconnected_user_id,
        )
