"""Authenticated matchmaking WebSocket server and multiplayer composition root."""

import asyncio
import json
import logging

import websockets

from config.multiplayer_settings import load_settings
from model.constants import PieceColor
from network.command_parser import CommandParser, CommandParseError, MoveCommand
from network.disconnect_manager import DisconnectManager
from network.game_registry import GameRegistry
from network.snapshot_serializer import serialize
from matchmaking.matchmaking_manager import MatchmakingManager
from services.auth_service import AuthError, AuthService
from services.elo_calculator import EloCalculator
from services.game_result_service import GameResultService
from storage.user_repository import UserRepository
from rooms.room_manager import RoomManager
from rooms.room_role import RoomRole
from rooms.game_room import RoomState
from observability.logging_service import LoggingService
from observability.game_event_auditor import GameEventAuditor

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
    """Routes authenticated sockets between lobby, queue and isolated games."""

    def __init__(self, host="localhost", port=8765, tick_ms=100, settings=None, repository=None):
        self.host, self.port, self.tick_ms = host, port, tick_ms
        self.settings = settings or load_settings()
        self.repository = repository or UserRepository(self.settings.database_path)
        self.repository.initialize()
        self.auth = AuthService(self.repository, self.settings)
        self.results = GameResultService(self.repository, EloCalculator(self.settings.elo))
        mm = self.settings.matchmaking
        self.matchmaking = MatchmakingManager(mm.elo_range, mm.queue_timeout_seconds)
        logging_service = LoggingService(self.settings.logging)
        self.logger = logging_service.create_logger("kung_fu_chess.server", self.settings.logging.server_log_path)
        self._log_event = logging_service.event
        self.games = GameRegistry(_DEFAULT_BOARD,
                                  event_auditor=GameEventAuditor(self.logger, self._log_event))
        self.rooms = RoomManager(self.settings.rooms)
        self.disconnects = DisconnectManager(self.settings.disconnect.grace_period_seconds)
        self._users: dict[object, object] = {}
        self._tokens: dict[object, str] = {}
        self._connections: set[object] = set()
        self._server = None

    @property
    def bound_port(self):
        return None if self._server is None else self._server.sockets[0].getsockname()[1]

    async def start(self):
        async with websockets.serve(self._handle_connection, self.host, self.port) as server:
            self._server = server
            self._log_event(self.logger, logging.INFO, "server_started", host=self.host, port=self.bound_port)
            await self._tick_loop()

    async def _handle_connection(self, websocket):
        self._connections.add(websocket)
        self._log_event(self.logger, logging.INFO, "connection_opened", connection_id=id(websocket))
        try:
            async for raw in websocket:
                await self._handle_message(websocket, raw)
        finally:
            await self._handle_disconnect(websocket)
            self._connections.discard(websocket)
            self._log_event(self.logger, logging.INFO, "connection_closed", connection_id=id(websocket))

    async def _handle_message(self, websocket, raw):
        if websocket not in self._users:
            await self._handle_unauthenticated(websocket, raw)
            return
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            message = None
        if isinstance(message, dict):
            action = message.get("type")
            if action == "join_queue":
                await self._join_queue(websocket)
            elif action == "leave_queue":
                await self._leave_queue(websocket)
            elif action == "create_room":
                await self._create_room(websocket)
            elif action == "join_room":
                await self._join_room(websocket, message)
            elif action == "leave_room":
                await self._leave_room(websocket)
            else:
                await self._send(websocket, {"type": "error", "reason": "unknown_action"})
            return
        await self._handle_game_command(websocket, raw)

    async def _handle_unauthenticated(self, websocket, raw):
        try:
            message = json.loads(raw)
            if message.get("type") == "reconnect":
                await self._reconnect(websocket, message)
                return
            if message.get("type") != "auth":
                raise AuthError("authentication_required")
            username, password = message["username"], message["password"]
            if message.get("mode") == "register":
                self.auth.register(username, password)
            user, token = self.auth.login(username, password)
            if any(active.id == user.id for active in self._users.values()):
                raise AuthError("user_already_connected")
            self._users[websocket], self._tokens[websocket] = user, token
            self._log_event(self.logger, logging.INFO, "authentication_succeeded",
                            user_id=user.id, username=user.username)
            await self._send(websocket, {"type": "auth_result", "username": user.username,
                                         "rating": user.rating, "token": token})
            await self._send(websocket, {"type": "lobby_ready"})
        except (AuthError, KeyError, TypeError, json.JSONDecodeError) as error:
            self._log_event(self.logger, logging.WARNING, "authentication_failed", reason=str(error))
            await self._send(websocket, {"type": "auth_error", "reason": str(error) or "invalid_auth_request"})

    async def _join_queue(self, websocket):
        user = self._users[websocket]
        if self.rooms.for_user(user.id):
            await self._send(websocket, {"type": "matchmaking_error", "reason": "already_in_game"})
            return
        try:
            self.matchmaking.join(user, websocket)
        except ValueError as error:
            await self._send(websocket, {"type": "matchmaking_error", "reason": str(error)})
            return
        await self._send(websocket, {"type": "queue_joined",
                                     "timeout_seconds": self.settings.matchmaking.queue_timeout_seconds})
        self._log_event(self.logger, logging.INFO, "queue_joined", user_id=user.id, rating=user.rating)
        await self._create_available_matches()

    async def _leave_queue(self, websocket):
        user = self._users[websocket]
        removed = self.matchmaking.leave(user.id)
        await self._send(websocket, {"type": "queue_left", "was_queued": removed is not None})

    async def _create_room(self, websocket):
        user = self._users[websocket]
        self.matchmaking.leave(user.id)
        try:
            room, member = self.rooms.create(user, websocket)
        except ValueError as error:
            await self._send(websocket, {"type": "room_error", "reason": str(error)})
            return
        self._log_event(self.logger, logging.INFO, "room_created", room_id=room.room_id,
                        user_id=user.id, role=member.role.value)
        await self._send(websocket, {"type": "room_created", "room_id": room.room_id,
                                     "role": member.role.value})
        await self._broadcast_room_state(room)

    async def _join_room(self, websocket, message):
        user = self._users[websocket]
        self.matchmaking.leave(user.id)
        try:
            room, member = self.rooms.join(message["room_id"], user, websocket)
        except (ValueError, KeyError) as error:
            await self._send(websocket, {"type": "room_error", "reason": str(error) or "invalid_room_request"})
            return
        self._log_event(self.logger, logging.INFO, "room_joined", room_id=room.room_id,
                        user_id=user.id, role=member.role.value)
        await self._send(websocket, {"type": "room_joined", "room_id": room.room_id,
                                     "role": member.role.value})
        if room.ready() and room.game_id is None:
            await self._start_room_game(room)
        elif room.game_id is not None:
            await self._announce_member(room, member)
        await self._broadcast_room_state(room)

    async def _leave_room(self, websocket):
        user = self._users[websocket]
        room = self.rooms.for_user(user.id)
        if room and room.state == RoomState.PLAYING and room.role_for(user.id).can_play:
            await self._send(websocket, {"type": "room_error", "reason": "cannot_leave_active_game"})
            return
        member = self.rooms.leave(user.id)
        await self._send(websocket, {"type": "room_left", "was_in_room": member is not None})
        if room:
            await self._broadcast_room_state(room)

    async def _create_available_matches(self):
        for white_entry, black_entry in self.matchmaking.find_matches():
            room = self.rooms.create_for_match(white_entry, black_entry)
            await self._start_room_game(room)

    async def _start_room_game(self, room):
        white = next(member for member in room.players() if member.role == RoomRole.WHITE)
        black = next(member for member in room.players() if member.role == RoomRole.BLACK)
        game = self.games.create(white.user, black.user, white.websocket, black.websocket)
        self.rooms.attach_game(room.room_id, game.game_id)
        room.state = RoomState.PLAYING
        self._log_event(self.logger, logging.INFO, "game_started", room_id=room.room_id, game_id=game.game_id)
        await self._announce_match(game)
        await self._broadcast_room_state(room)

    async def _announce_match(self, game):
        room = self._room_for_game(game.game_id)
        for member in room.players():
            await self._announce_member(room, member)
        await self._broadcast_snapshot(game)

    async def _announce_member(self, room, member):
        players = room.players()
        opponent = next((candidate for candidate in players if candidate.user.id != member.user.id), None)
        await self._safe_send(member.websocket, {
            "type": "match_found", "game_id": room.game_id, "room_id": room.room_id,
            "role": member.role.value, "color": member.role.color_value,
            "opponent": None if opponent is None else {"username": opponent.user.username,
                                                         "rating": opponent.user.rating},
        })

    async def _broadcast_room_state(self, room):
        payload = {"type": "room_state", "room_id": room.room_id,
                   "state": room.state.value, "members": room.members_payload()}
        await asyncio.gather(*(self._safe_send(connection, payload) for connection in room.connections()))

    def _room_for_game(self, game_id):
        return self.rooms.for_game(game_id)

    async def _handle_game_command(self, websocket, raw):
        user = self._users[websocket]
        room = self.rooms.for_user(user.id)
        game = self.games.get(room.game_id) if room and room.game_id else None
        if not game or game.finished:
            await self._send(websocket, {"type": "error", "reason": "not_in_active_game"})
            return
        role = room.role_for(user.id)
        if role == RoomRole.SPECTATOR:
            self._log_event(self.logger, logging.WARNING, "spectator_command_rejected",
                            room_id=room.room_id, user_id=user.id)
            await self._send(websocket, {"type": "error", "reason": "spectator_read_only"})
            return
        try:
            command = CommandParser.parse(raw)
        except CommandParseError as error:
            await self._send(websocket, {"type": "error", "reason": str(error)})
            return
        source = command.source if isinstance(command, MoveCommand) else command.position
        if not game.is_authorized(user.id, source):
            await self._send(websocket, {"type": "error", "reason": "not_your_piece"})
            return
        result = (game.engine.request_move(command.source, command.destination)
                  if isinstance(command, MoveCommand) else game.engine.request_jump(command.position))
        if not result.is_accepted:
            await self._send(websocket, {"type": "error", "reason": result.reason})
        else:
            self._log_event(self.logger, logging.INFO, "game_command_accepted",
                            room_id=room.room_id, game_id=game.game_id, user_id=user.id,
                            command_type=type(command).__name__)

    async def _handle_disconnect(self, websocket):
        queued = self.matchmaking.remove_connection(websocket)
        user = self._users.pop(websocket, None)
        self._tokens.pop(websocket, None)
        if queued or user is None:
            return
        room = self.rooms.for_user(user.id)
        if room:
            member = room.disconnect(user.id)
            game = self.games.get(room.game_id) if room.game_id else None
            if game and not game.finished and member.role.can_play:
                game.disconnect(user.id)
                self.disconnects.start(game.game_id, user.id)
                await self._broadcast_to_room(room, {"type": "opponent_disconnected",
                    "username": user.username,
                    "remaining_seconds": int(self.settings.disconnect.grace_period_seconds)}, exclude_user=user.id)
            self._log_event(self.logger, logging.INFO, "room_member_disconnected",
                            room_id=room.room_id, user_id=user.id, role=member.role.value)

    async def _reconnect(self, websocket, message):
        token, game_id = message["token"], message["game_id"]
        user = self.auth.user_for_token(token)
        game = self.games.get(game_id)
        room = self.rooms.for_user(user.id) if user else None
        member = room.member(user.id) if room else None
        if user is None or game is None or member is None or room.game_id != game_id or game.finished:
            raise AuthError("invalid_reconnect")
        if member.websocket is not None:
            raise AuthError("player_already_connected")
        if member.role.can_play and not self.disconnects.cancel(game_id, user.id):
            raise AuthError("reconnect_window_expired")
        room.reconnect(user.id, websocket)
        if member.role.can_play:
            game.reconnect(user.id, websocket)
        self._users[websocket], self._tokens[websocket] = user, token
        await self._send(websocket, {"type": "reconnect_success", "username": user.username,
                                     "rating": user.rating, "game_id": game_id, "room_id": room.room_id,
                                     "role": member.role.value, "color": member.role.color_value})
        await self._send_snapshot(websocket, game)
        await self._broadcast_to_room(room, {"type": "opponent_reconnected", "username": user.username},
                                      exclude_user=user.id)

    async def _tick_loop(self):
        while True:
            await asyncio.sleep(self.tick_ms / 1000)
            for player in self.matchmaking.expired():
                await self._safe_send(player.websocket, {"type": "matchmaking_timeout"})
            await self._create_available_matches()
            for game in self.games.all():
                game.tick(self.tick_ms)
                if game.pending_game_over and not game.result_applied:
                    await self._finish_normal_game(game)
                if not game.finished:
                    await self._broadcast_snapshot(game)
            await self._process_disconnects()

    async def _process_disconnects(self):
        for state, remaining in self.disconnects.updates():
            game = self.games.get(state.game_id)
            if game and not game.finished:
                opponent = game.opponent_of(state.user_id)
                room = self._room_for_game(game.game_id)
                await self._broadcast_to_room(room, {"type": "opponent_disconnected",
                    "username": game.slot_for_user(state.user_id).user.username,
                    "remaining_seconds": remaining}, exclude_user=state.user_id)
        for state in self.disconnects.expired():
            game = self.games.get(state.game_id)
            if game and not game.finished:
                winner = game.opponent_of(state.user_id)
                await self._finish_game(game, winner.user.id, "technical_forfeit")

    async def _finish_normal_game(self, game):
        winner_color = game.pending_game_over.winner
        winner = next((slot for slot in game.players.values()
                       if (winner_color == "WHITE" and slot.color == PieceColor.WHITE)
                       or (winner_color == "BLACK" and slot.color == PieceColor.BLACK)), None)
        await self._finish_game(game, winner.user.id if winner else None, "king_capture")

    async def _finish_game(self, game, winner_user_id, reason):
        if game.result_applied:
            return
        game.result_applied = game.finished = True
        room = self._room_for_game(game.game_id)
        room.state = RoomState.FINISHED
        self._log_event(self.logger, logging.INFO, "game_finished", room_id=room.room_id,
                        game_id=game.game_id, winner_user_id=winner_user_id, reason=reason)
        white = next(slot for slot in game.players.values() if slot.color == PieceColor.WHITE)
        black = next(slot for slot in game.players.values() if slot.color == PieceColor.BLACK)
        white_outcome = "draw" if winner_user_id is None else "win" if winner_user_id == white.user.id else "loss"
        white_rating, black_rating = self.results.record(white.user, black.user, white_outcome)
        winner_slot = None if winner_user_id is None else game.slot_for_user(winner_user_id)
        winner_payload = None if winner_slot is None else {
            "username": winner_slot.user.username, "color": winner_slot.color.name}
        for slot, rating in ((white, white_rating), (black, black_rating)):
            outcome = "draw" if winner_user_id is None else "win" if slot.user.id == winner_user_id else "loss"
            await self._safe_send(slot.websocket, {"type": "game_result", "game_id": game.game_id,
                                                    "outcome": outcome, "reason": reason, "rating": rating,
                                                    "winner": winner_payload})
        for spectator in room.spectators():
            await self._safe_send(spectator.websocket, {"type": "game_result", "game_id": game.game_id,
                "outcome": "spectator", "reason": reason, "rating": spectator.user.rating,
                "winner": winner_payload})
        # The regular tick loop stops broadcasting as soon as a game is marked
        # finished. Push one authoritative final frame so clients do not remain
        # frozen on an in-flight pre-capture snapshot.
        await self._broadcast_snapshot(game)

    async def _broadcast_snapshot(self, game):
        sequence, snapshot = game.next_snapshot()
        payload = {"type": "snapshot", "game_id": game.game_id, "sequence": sequence,
                   "data": serialize(snapshot)}
        room = self._room_for_game(game.game_id)
        connections = room.connections() if room else tuple(slot.websocket for slot in game.players.values())
        await asyncio.gather(*(self._safe_send(connection, payload) for connection in connections))

    async def _broadcast_to_room(self, room, payload, exclude_user=None):
        connections = tuple(member.websocket for member in room.members()
                            if member.websocket is not None and member.user.id != exclude_user)
        await asyncio.gather(*(self._safe_send(connection, payload) for connection in connections))

    async def _send_snapshot(self, websocket, game):
        sequence, snapshot = game.next_snapshot()
        await self._send(websocket, {"type": "snapshot", "game_id": game.game_id,
                                     "sequence": sequence, "data": serialize(snapshot)})

    async def _send(self, websocket, payload):
        self._log_event(self.logger, logging.DEBUG, "network_message_sent",
                        connection_id=id(websocket), message_type=payload.get("type"))
        await websocket.send(json.dumps(payload))

    async def _safe_send(self, websocket, payload):
        if websocket is None:
            return
        try:
            await self._send(websocket, payload)
        except websockets.ConnectionClosed:
            pass


async def _run():
    logging.basicConfig(level=logging.INFO)
    await GameServer().start()


if __name__ == "__main__":
    asyncio.run(_run())
