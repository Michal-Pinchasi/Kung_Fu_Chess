"""WebSocket serialization and fan-out operations."""

import asyncio
import json
import logging

import websockets

from network.snapshot_serializer import serialize


class MessageSender:
    """Sends protocol messages without owning game or connection state."""

    def __init__(self, logger, event_writer):
        self._logger = logger
        self._write_event = event_writer

    async def send(self, websocket, payload) -> None:
        self._write_event(
            self._logger,
            logging.DEBUG,
            "network_message_sent",
            connection_id=id(websocket),
            message_type=payload.get("type"),
        )
        await websocket.send(json.dumps(payload))

    async def safe_send(self, websocket, payload) -> None:
        if websocket is None:
            return
        try:
            await self.send(websocket, payload)
        except websockets.ConnectionClosed:
            pass

    async def broadcast_room(self, room, payload, exclude_user_id=None) -> None:
        connections = tuple(
            member.websocket
            for member in room.members()
            if member.websocket is not None and member.user.id != exclude_user_id
        )
        await asyncio.gather(*(self.safe_send(connection, payload) for connection in connections))

    async def broadcast_room_state(self, room) -> None:
        payload = {
            "type": "room_state",
            "room_id": room.room_id,
            "state": room.state.value,
            "members": room.members_payload(),
        }
        await asyncio.gather(
            *(self.safe_send(connection, payload) for connection in room.connections())
        )

    async def send_snapshot(self, websocket, game) -> None:
        sequence, snapshot = game.next_snapshot()
        await self.send(
            websocket,
            {
                "type": "snapshot",
                "game_id": game.game_id,
                "sequence": sequence,
                "data": serialize(snapshot),
            },
        )

    async def broadcast_snapshot(self, game, room=None) -> None:
        sequence, snapshot = game.next_snapshot()
        payload = {
            "type": "snapshot",
            "game_id": game.game_id,
            "sequence": sequence,
            "data": serialize(snapshot),
        }
        connections = (
            room.connections()
            if room
            else tuple(slot.websocket for slot in game.players.values())
        )
        await asyncio.gather(*(self.safe_send(connection, payload) for connection in connections))
