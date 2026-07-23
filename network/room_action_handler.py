"""Authenticated private-room action handling."""

import logging

from rooms.game_room import RoomState


class RoomActionHandler:
    """Creates, joins and leaves rooms while lifecycle logic stays delegated."""

    def __init__(
        self, matchmaking, rooms, lifecycle, sender, logger, event_writer
    ):
        self._matchmaking = matchmaking
        self._rooms = rooms
        self._lifecycle = lifecycle
        self._sender = sender
        self._logger = logger
        self._write_event = event_writer

    async def handle(self, websocket, user, message) -> bool:
        action = message.get("type")
        if action == "create_room":
            await self.create(websocket, user)
            return True
        if action == "join_room":
            await self.join(websocket, user, message)
            return True
        if action == "leave_room":
            await self.leave(websocket, user)
            return True
        return False

    async def create(self, websocket, user) -> None:
        self._matchmaking.leave(user.id)
        try:
            room, member = self._rooms.create(user, websocket)
        except ValueError as error:
            await self._sender.send(
                websocket, {"type": "room_error", "reason": str(error)}
            )
            return
        self._audit("room_created", room, member)
        await self._sender.send(
            websocket,
            {
                "type": "room_created",
                "room_id": room.room_id,
                "role": member.role.value,
            },
        )
        await self._sender.broadcast_room_state(room)

    async def join(self, websocket, user, message) -> None:
        self._matchmaking.leave(user.id)
        try:
            room, member = self._rooms.join(message["room_id"], user, websocket)
        except (ValueError, KeyError) as error:
            await self._sender.send(
                websocket,
                {
                    "type": "room_error",
                    "reason": str(error) or "invalid_room_request",
                },
            )
            return
        self._audit("room_joined", room, member)
        await self._sender.send(
            websocket,
            {
                "type": "room_joined",
                "room_id": room.room_id,
                "role": member.role.value,
            },
        )
        if room.ready() and room.game_id is None:
            await self._lifecycle.start_room_game(room)
        elif room.game_id is not None:
            await self._lifecycle.announce_member(room, member)
        await self._sender.broadcast_room_state(room)

    async def leave(self, websocket, user) -> None:
        room = self._rooms.for_user(user.id)
        if (
            room
            and room.state == RoomState.PLAYING
            and room.role_for(user.id).can_play
        ):
            await self._sender.send(
                websocket,
                {"type": "room_error", "reason": "cannot_leave_active_game"},
            )
            return
        member = self._rooms.leave(user.id)
        await self._sender.send(
            websocket, {"type": "room_left", "was_in_room": member is not None}
        )
        if room:
            await self._sender.broadcast_room_state(room)

    def _audit(self, event, room, member) -> None:
        self._write_event(
            self._logger,
            logging.INFO,
            event,
            room_id=room.room_id,
            user_id=member.user.id,
            role=member.role.value,
        )
