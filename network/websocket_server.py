"""
Local multiplayer WebSocket server for Kung Fu Chess.

The composition root for the network layer — the WebSocket counterpart to
view/ui/app.py (GUI) and main.py (headless CLI). Wires together GameEngine,
MessageBus, SessionManager, and CommandParser: assigns each of up to two
connecting clients a player color, routes incoming move/jump commands
through the engine after authorizing them against the live board, and
periodically broadcasts the serialized game snapshot to every connected
client so their screens stay in sync in real time.
"""

import asyncio
import json
import logging

import websockets

from storage.board_parser import BoardParser
from engin.game_engine import GameEngine
from events.message_bus import MessageBus
from events.game_events import GAME_OVER, GameOverEvent
from network.session_manager import SessionManager
from network.command_parser import CommandParser, CommandParseError, MoveCommand
from network.snapshot_serializer import serialize
from config.multiplayer_settings import load_settings
from storage.user_repository import UserRepository
from services.auth_service import AuthService, AuthError
from services.elo_calculator import EloCalculator
from services.game_result_service import GameResultService

logger = logging.getLogger(__name__)

_DEFAULT_BOARD = """\
wR wN wB wQ wK wB wN wR
wP wP wP wP wP wP wP wP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
bP bP bP bP bP bP bP bP
bR bN bB bQ bK bB bN bR"""


class GameServer:
    """WebSocket server hosting a single real-time Kung Fu Chess match.

    Does not itself contain chess rules, timing logic, or session/color
    policy — those all live in GameEngine/RealTimeArbiter/RuleEngine and
    SessionManager respectively. This class only wires them to the network:
    it never mutates the board directly, and never decides move legality
    or ownership itself.
    """

    def __init__(self, host: str = "localhost", port: int = 8765, tick_ms: int = 100,
                 settings=None, repository=None):
        """Create a server that will listen on host:port once start() runs.

        Parameters
        ----------
        host : str
            Interface to listen on. "localhost" restricts connections to
            the local machine, per Phase 1's local-multiplayer scope.
        port : int
            TCP port to listen on.
        tick_ms : int
            How often, in milliseconds, to advance the simulated game clock
            (GameEngine.wait) and broadcast a fresh snapshot to all clients.
        """
        self.host = host
        self.port = port
        self.tick_ms = tick_ms

        self.bus = MessageBus()
        self.settings = settings or load_settings()
        self.repository = repository or UserRepository(self.settings.database_path)
        self.repository.initialize()
        self.auth = AuthService(self.repository, self.settings)
        self.results = GameResultService(self.repository, EloCalculator(self.settings.elo))
        board = BoardParser.parse(_DEFAULT_BOARD)
        self.engine = GameEngine(board, message_bus=self.bus)
        self.sessions = SessionManager()
        self._connections: set = set()
        self._users: dict = {}
        self._ratings_applied = False
        self._server = None

        self.bus.subscribe(GAME_OVER, self._on_game_over)

    @property
    def bound_port(self):
        """Return the TCP port the server is actually listening on, or None before start().

        Useful when port=0 was requested (let the OS pick a free port),
        e.g. in tests that need to know which port to connect to.
        """
        if self._server is None:
            return None
        return self._server.sockets[0].getsockname()[1]

    async def start(self) -> None:
        """Start listening for connections and run the simulation tick loop forever.

        Runs until the enclosing task is cancelled (e.g. by the caller
        cancelling the asyncio task this coroutine is scheduled on).
        """
        async with websockets.serve(self._handle_connection, self.host, self.port) as server:
            self._server = server
            logger.info("GameServer listening on %s:%d", self.host, self.bound_port)
            await self._tick_loop()

    async def _handle_connection(self, websocket) -> None:
        """Assign a connecting client a color (or reject it) and process its messages.

        Called once per incoming connection by the websockets library.
        Runs for the lifetime of that connection.
        """
        self._connections.add(websocket)

        try:
            async for raw_message in websocket:
                await self._handle_message(websocket, raw_message)
        finally:
            self.sessions.release(websocket)
            self._users.pop(websocket, None)
            self._connections.discard(websocket)

    async def _handle_message(self, websocket, raw_message: str) -> None:
        """Parse, authorize, and apply one incoming wire command from a client.

        Sends a JSON error back to that single client (never broadcast) on
        a parse failure, an unauthorized command, or a rejected engine
        request. The engine is only ever touched once the command has
        parsed successfully and passed ownership authorization.
        """
        if websocket not in self._users:
            await self._handle_authentication(websocket, raw_message)
            return

        try:
            command = CommandParser.parse(raw_message)
        except CommandParseError as error:
            await self._send(websocket, {"type": "error", "reason": str(error)})
            return

        source = command.source if isinstance(command, MoveCommand) else command.position
        if not self.sessions.is_authorized(websocket, self.engine.board, source):
            await self._send(websocket, {"type": "error", "reason": "not_your_piece"})
            return

        if isinstance(command, MoveCommand):
            result = self.engine.request_move(command.source, command.destination)
        else:
            result = self.engine.request_jump(command.position)

        if not result.is_accepted:
            await self._send(websocket, {"type": "error", "reason": result.reason})

    async def _handle_authentication(self, websocket, raw_message: str) -> None:
        """Authenticate a socket before it receives a player color or game state."""
        try:
            message = json.loads(raw_message)
            if message.get("type") != "auth":
                raise AuthError("authentication_required")
            username, password = message["username"], message["password"]
            if message.get("mode") == "register":
                self.auth.register(username, password)
            user, token = self.auth.login(username, password)
            if any(active_user.id == user.id for active_user in self._users.values()):
                raise AuthError("user_already_in_game")
            color = self.sessions.assign_color(websocket)
            if color is None:
                await self._send(websocket, {"type": "error", "reason": "game_full"})
                return
            self._users[websocket] = user
            await self._send(websocket, {
                "type": "auth_result", "username": user.username, "rating": user.rating, "token": token,
            })
            await self._send(websocket, {"type": "assigned_color", "color": color.value})
            await self._send(websocket, {"type": "snapshot", "data": serialize(self.engine.snapshot())})
        except (AuthError, KeyError, TypeError, json.JSONDecodeError) as error:
            reason = str(error) if str(error) else "invalid_auth_request"
            await self._send(websocket, {"type": "auth_error", "reason": reason})

    async def _tick_loop(self) -> None:
        """Advance simulated time and broadcast a fresh snapshot on a fixed interval."""
        while True:
            await asyncio.sleep(self.tick_ms / 1000)
            self.engine.wait(self.tick_ms)
            await self._broadcast_snapshot()

    async def _broadcast_snapshot(self) -> None:
        """Send the current serialized game snapshot to every connected client."""
        if not self._connections:
            return
        message = json.dumps({"type": "snapshot", "data": serialize(self.engine.snapshot())})
        await asyncio.gather(
            *(self._send_raw(ws, message) for ws in list(self._connections)),
            return_exceptions=True,
        )

    def _on_game_over(self, event: GameOverEvent) -> None:
        """MessageBus handler for GAME_OVER: broadcast immediately, don't wait for the next tick.

        MessageBus handlers are always called synchronously, so this
        schedules the actual async broadcast as a background task rather
        than awaiting it directly.
        """
        if not self._ratings_applied:
            self._ratings_applied = True
            asyncio.create_task(self._record_ratings_and_broadcast(event))
        else:
            asyncio.create_task(self._broadcast_snapshot())

    async def _record_ratings_and_broadcast(self, event: GameOverEvent) -> None:
        """Persist ELO once, then make the post-game ratings visible to both players."""
        white_socket = next((ws for ws in self._users if self.sessions.color_for(ws)
                             and self.sessions.color_for(ws).value == "w"), None)
        black_socket = next((ws for ws in self._users if self.sessions.color_for(ws)
                             and self.sessions.color_for(ws).value == "b"), None)
        if white_socket is not None and black_socket is not None:
            white, black = self._users[white_socket], self._users[black_socket]
            white_outcome = "win" if event.winner == "WHITE" else "loss" if event.winner == "BLACK" else "draw"
            white_rating, black_rating = self.results.record(white, black, white_outcome)
            await self._send(white_socket, {"type": "game_result", "outcome": white_outcome, "rating": white_rating})
            black_outcome = {"win": "loss", "loss": "win", "draw": "draw"}[white_outcome]
            await self._send(black_socket, {"type": "game_result", "outcome": black_outcome, "rating": black_rating})
        await self._broadcast_snapshot()

    async def _send(self, websocket, payload: dict) -> None:
        """Serialize payload to JSON and send it to a single client."""
        await self._send_raw(websocket, json.dumps(payload))

    @staticmethod
    async def _send_raw(websocket, message: str) -> None:
        """Send a raw JSON string to a single client, ignoring a closed connection.

        A client that disconnected between being listed and being sent to
        raises ConnectionClosed here; that race is expected and harmless —
        _handle_connection's own finally block is what actually removes a
        disconnected client from self._connections.
        """
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass


async def _run() -> None:
    """Start a GameServer with default settings and run it until interrupted."""
    logging.basicConfig(level=logging.INFO)
    await GameServer().start()


if __name__ == "__main__":
    asyncio.run(_run())
