"""WebSocket host and composition root for the multiplayer server."""

import asyncio
import json
import logging

import websockets

from config.multiplayer_settings import load_settings
from network.server_composition import build_server_components


class GameServer:
    """Hosts connections and routes incoming messages to focused handlers."""

    def __init__(
        self, host="localhost", port=8765, tick_ms=100, settings=None, repository=None
    ):
        self.host, self.port, self.tick_ms = host, port, tick_ms
        self.settings = settings or load_settings()
        components = build_server_components(self.settings, repository)
        self.repository = components.repository
        self.auth, self.results = components.auth, components.results
        self.matchmaking = components.matchmaking
        self.logger, self._log_event = components.logger, components.log_event
        self.games, self.rooms = components.games, components.rooms
        self.disconnects, self._sender = components.disconnects, components.sender
        self._authentication = components.authentication
        self._matchmaking_handler = components.matchmaking_handler
        self._room_actions, self._commands = components.room_actions, components.commands
        self._connection_lifecycle = components.connection_lifecycle
        self._lifecycle = components.lifecycle
        # Public aliases retained for callers that inspect active identities.
        self._users = self._authentication.users
        self._tokens = self._authentication.tokens
        self._connections: set[object] = set()
        self._server = None

    @property
    def bound_port(self):
        return (
            None
            if self._server is None
            else self._server.sockets[0].getsockname()[1]
        )

    async def start(self) -> None:
        async with websockets.serve(
            self._handle_connection, self.host, self.port
        ) as server:
            self._server = server
            self._log_event(
                self.logger,
                logging.INFO,
                "server_started",
                host=self.host,
                port=self.bound_port,
            )
            await self._tick_loop()

    async def _handle_connection(self, websocket) -> None:
        self._connections.add(websocket)
        self._log_event(
            self.logger,
            logging.INFO,
            "connection_opened",
            connection_id=id(websocket),
        )
        try:
            async for raw in websocket:
                await self._handle_message(websocket, raw)
        finally:
            await self._handle_disconnect(websocket)
            self._connections.discard(websocket)
            self._log_event(
                self.logger,
                logging.INFO,
                "connection_closed",
                connection_id=id(websocket),
            )

    async def _handle_message(self, websocket, raw) -> None:
        if websocket not in self._users:
            await self._authentication.handle(websocket, raw)
            return
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            message = None
        user = self._users[websocket]
        if isinstance(message, dict):
            action = message.get("type")
            handled = await self._matchmaking_handler.handle(
                websocket, user, action
            )
            if not handled:
                handled = await self._room_actions.handle(websocket, user, message)
            if not handled:
                await self._sender.send(
                    websocket, {"type": "error", "reason": "unknown_action"}
                )
            return
        await self._commands.handle(websocket, user, raw)

    async def _handle_disconnect(self, websocket) -> None:
        queued = self.matchmaking.remove_connection(websocket)
        user = self._authentication.remove(websocket)
        if queued or user is None:
            return
        await self._connection_lifecycle.disconnect(user)

    async def _tick_loop(self) -> None:
        while True:
            await asyncio.sleep(self.tick_ms / 1000)
            await self._lifecycle.tick(self.tick_ms)

    # Compatibility helpers used by older integrations.
    async def _send(self, websocket, payload) -> None:
        await self._sender.send(websocket, payload)

    async def _safe_send(self, websocket, payload) -> None:
        await self._sender.safe_send(websocket, payload)


async def _run():
    logging.basicConfig(level=logging.INFO)
    await GameServer().start()


if __name__ == "__main__":
    asyncio.run(_run())
