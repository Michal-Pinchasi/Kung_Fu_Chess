"""Authentication and authenticated connection identity handling."""

import json
import logging

from services.auth_service import AuthError


class AuthenticationHandler:
    """Authenticates sockets and restores eligible disconnected sessions."""

    def __init__(self, auth_service, games, rooms, disconnects, sender, logger, event_writer):
        self._auth = auth_service
        self._games = games
        self._rooms = rooms
        self._disconnects = disconnects
        self._sender = sender
        self._logger = logger
        self._write_event = event_writer
        self.users: dict[object, object] = {}
        self.tokens: dict[object, str] = {}

    async def handle(self, websocket, raw) -> None:
        try:
            message = json.loads(raw)
            if message.get("type") == "reconnect":
                await self.reconnect(websocket, message)
                return
            if message.get("type") != "auth":
                raise AuthError("authentication_required")
            username, password = message["username"], message["password"]
            if message.get("mode") == "register":
                self._auth.register(username, password)
            user, token = self._auth.login(username, password)
            if any(active.id == user.id for active in self.users.values()):
                raise AuthError("user_already_connected")
            self.users[websocket], self.tokens[websocket] = user, token
            self._write_event(
                self._logger,
                logging.INFO,
                "authentication_succeeded",
                user_id=user.id,
                username=user.username,
            )
            await self._sender.send(
                websocket,
                {
                    "type": "auth_result",
                    "username": user.username,
                    "rating": user.rating,
                    "token": token,
                },
            )
            if await self._resume_authenticated(websocket, user, token):
                return
            await self._sender.send(websocket, {"type": "lobby_ready"})
        except (AuthError, KeyError, TypeError, json.JSONDecodeError) as error:
            self._write_event(
                self._logger, logging.WARNING, "authentication_failed", reason=str(error)
            )
            await self._sender.send(
                websocket,
                {"type": "auth_error", "reason": str(error) or "invalid_auth_request"},
            )

    async def reconnect(self, websocket, message) -> None:
        token, game_id = message["token"], message["game_id"]
        user = self._auth.user_for_token(token)
        game = self._games.get(game_id)
        room = self._rooms.for_user(user.id) if user else None
        member = room.member(user.id) if room else None
        if not self._is_resumable(user, game, room, member, game_id):
            raise AuthError("invalid_reconnect")
        if member.websocket is not None:
            raise AuthError("player_already_connected")
        if member.role.can_play and not self._disconnects.cancel(game_id, user.id):
            raise AuthError("reconnect_window_expired")
        await self._restore(websocket, user, token, game, room, member)

    async def _resume_authenticated(self, websocket, user, token) -> bool:
        game = self._games.for_user(user.id)
        room = self._rooms.for_user(user.id)
        member = room.member(user.id) if room else None
        game_id = game.game_id if game else None
        if not self._is_resumable(user, game, room, member, game_id):
            return False
        if member.websocket is not None:
            return False
        if member.role.can_play and not self._disconnects.cancel(game_id, user.id):
            return False
        await self._restore(websocket, user, token, game, room, member)
        self._write_event(
            self._logger,
            logging.INFO,
            "game_resumed_after_login",
            user_id=user.id,
            game_id=game_id,
            room_id=room.room_id,
        )
        return True

    @staticmethod
    def _is_resumable(user, game, room, member, game_id) -> bool:
        return (
            user is not None
            and game is not None
            and room is not None
            and member is not None
            and room.game_id == game_id
            and not game.finished
        )

    async def _restore(self, websocket, user, token, game, room, member) -> None:
        room.reconnect(user.id, websocket)
        if member.role.can_play:
            game.reconnect(user.id, websocket)
        self.users[websocket], self.tokens[websocket] = user, token
        await self._sender.send(
            websocket,
            {
                "type": "reconnect_success",
                "username": user.username,
                "rating": user.rating,
                "game_id": game.game_id,
                "room_id": room.room_id,
                "role": member.role.value,
                "color": member.role.color_value,
            },
        )
        await self._sender.send_snapshot(websocket, game)
        await self._sender.broadcast_room(
            room,
            {"type": "opponent_reconnected", "username": user.username},
            exclude_user_id=user.id,
        )

    def remove(self, websocket):
        user = self.users.pop(websocket, None)
        self.tokens.pop(websocket, None)
        return user
