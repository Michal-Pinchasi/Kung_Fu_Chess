"""Authorization and execution of commands sent during active games."""

import logging

from network.command_parser import CommandParser, CommandParseError, MoveCommand
from rooms.room_role import RoomRole


class GameCommandHandler:
    """Validates one player's command and passes it to the correct engine."""

    def __init__(self, games, rooms, sender, logger, event_writer):
        self._games = games
        self._rooms = rooms
        self._sender = sender
        self._logger = logger
        self._write_event = event_writer

    async def handle(self, websocket, user, raw) -> None:
        room = self._rooms.for_user(user.id)
        game = self._games.get(room.game_id) if room and room.game_id else None
        if not game or game.finished:
            await self._sender.send(websocket, {"type": "error", "reason": "not_in_active_game"})
            return
        role = room.role_for(user.id)
        if role == RoomRole.SPECTATOR:
            self._write_event(
                self._logger,
                logging.WARNING,
                "spectator_command_rejected",
                room_id=room.room_id,
                user_id=user.id,
            )
            await self._sender.send(websocket, {"type": "error", "reason": "spectator_read_only"})
            return
        try:
            command = CommandParser.parse(raw)
        except CommandParseError as error:
            await self._sender.send(websocket, {"type": "error", "reason": str(error)})
            return
        source = command.source if isinstance(command, MoveCommand) else command.position
        if not game.is_authorized(user.id, source):
            await self._sender.send(websocket, {"type": "error", "reason": "not_your_piece"})
            return
        result = (
            game.engine.request_move(command.source, command.destination)
            if isinstance(command, MoveCommand)
            else game.engine.request_jump(command.position)
        )
        if not result.is_accepted:
            await self._sender.send(websocket, {"type": "error", "reason": result.reason})
            return
        self._write_event(
            self._logger,
            logging.INFO,
            "game_command_accepted",
            room_id=room.room_id,
            game_id=game.game_id,
            user_id=user.id,
            command_type=type(command).__name__,
        )
