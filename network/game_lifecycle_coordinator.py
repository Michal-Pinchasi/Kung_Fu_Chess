"""Active-game creation and ticking coordination."""

import logging

from rooms.game_room import RoomState
from rooms.room_role import RoomRole


class GameLifecycleCoordinator:
    """Starts and advances games while delegating results and disconnects."""

    def __init__(
        self,
        games,
        rooms,
        matchmaking,
        result_coordinator,
        connection_lifecycle,
        sender,
        logger,
        event_writer,
    ):
        self._games = games
        self._rooms = rooms
        self._matchmaking = matchmaking
        self._results = result_coordinator
        self._connections = connection_lifecycle
        self._sender = sender
        self._logger = logger
        self._write_event = event_writer

    async def create_available_matches(self) -> None:
        for white_entry, black_entry in self._matchmaking.find_matches():
            room = self._rooms.create_for_match(white_entry, black_entry)
            await self.start_room_game(room)

    async def start_room_game(self, room) -> None:
        white = next(
            member for member in room.players() if member.role == RoomRole.WHITE
        )
        black = next(
            member for member in room.players() if member.role == RoomRole.BLACK
        )
        game = self._games.create(
            white.user, black.user, white.websocket, black.websocket
        )
        self._rooms.attach_game(room.room_id, game.game_id)
        room.state = RoomState.PLAYING
        self._write_event(
            self._logger,
            logging.INFO,
            "game_started",
            room_id=room.room_id,
            game_id=game.game_id,
        )
        for member in room.players():
            await self.announce_member(room, member)
        await self._sender.broadcast_snapshot(game, room)
        await self._sender.broadcast_room_state(room)

    async def announce_member(self, room, member) -> None:
        opponent = next(
            (
                candidate
                for candidate in room.players()
                if candidate.user.id != member.user.id
            ),
            None,
        )
        await self._sender.safe_send(
            member.websocket,
            {
                "type": "match_found",
                "game_id": room.game_id,
                "room_id": room.room_id,
                "role": member.role.value,
                "color": member.role.color_value,
                "opponent": (
                    None
                    if opponent is None
                    else {
                        "username": opponent.user.username,
                        "rating": opponent.user.rating,
                    }
                ),
            },
        )

    async def tick(self, milliseconds: int) -> None:
        for player in self._matchmaking.expired():
            await self._sender.safe_send(
                player.websocket, {"type": "matchmaking_timeout"}
            )
        await self.create_available_matches()
        for game in self._games.all():
            game.tick(milliseconds)
            if game.pending_game_over and not game.result_applied:
                await self._results.finish_captured_king(game)
            if not game.finished:
                await self._sender.broadcast_snapshot(
                    game, self._rooms.for_game(game.game_id)
                )
        await self._connections.process()
