"""Completed-game result calculation, persistence and notification."""

import logging

from model.constants import PieceColor
from rooms.game_room import RoomState


class GameResultCoordinator:
    """Finalizes a game exactly once and publishes its persisted result."""

    def __init__(
        self, games, rooms, disconnects, results, sender, logger, event_writer
    ):
        self._games = games
        self._rooms = rooms
        self._disconnects = disconnects
        self._results = results
        self._sender = sender
        self._logger = logger
        self._write_event = event_writer

    async def finish_captured_king(self, game) -> None:
        winner_color = game.pending_game_over.winner
        winner = next(
            (
                slot
                for slot in game.players.values()
                if self._slot_matches_winner(slot, winner_color)
            ),
            None,
        )
        await self.finish(
            game, winner.user.id if winner else None, "king_capture"
        )

    async def finish(self, game, winner_user_id, reason) -> None:
        if game.result_applied:
            return
        game.result_applied = game.finished = True
        room = self._rooms.for_game(game.game_id)
        room.state = RoomState.FINISHED
        self._write_event(
            self._logger,
            logging.INFO,
            "game_finished",
            room_id=room.room_id,
            game_id=game.game_id,
            winner_user_id=winner_user_id,
            reason=reason,
        )
        white, black = self._players_by_color(game)
        white_outcome = self._outcome(white.user.id, winner_user_id)
        white_rating, black_rating = self._results.record(
            white.user, black.user, white_outcome
        )
        winner_payload = self._winner_payload(game, winner_user_id)
        # Release lookup indexes before notifying clients. Once GAME OVER is
        # visible, every participant must already be eligible for a new room.
        self._disconnects.cancel_game(game.game_id)
        self._games.remove(game.game_id)
        self._rooms.remove(room.room_id)
        await self._send_player_results(
            game,
            ((white, white_rating), (black, black_rating)),
            winner_user_id,
            winner_payload,
            reason,
        )
        await self._send_spectator_results(
            room, game, winner_payload, reason
        )
        await self._sender.broadcast_snapshot(game, room)
        self._write_event(
            self._logger,
            logging.INFO,
            "finished_game_resources_released",
            room_id=room.room_id,
            game_id=game.game_id,
        )

    @staticmethod
    def _slot_matches_winner(slot, winner_color) -> bool:
        return (
            winner_color == "WHITE" and slot.color == PieceColor.WHITE
        ) or (
            winner_color == "BLACK" and slot.color == PieceColor.BLACK
        )

    @staticmethod
    def _players_by_color(game):
        white = next(
            slot for slot in game.players.values() if slot.color == PieceColor.WHITE
        )
        black = next(
            slot for slot in game.players.values() if slot.color == PieceColor.BLACK
        )
        return white, black

    @staticmethod
    def _outcome(user_id, winner_user_id) -> str:
        if winner_user_id is None:
            return "draw"
        return "win" if user_id == winner_user_id else "loss"

    @staticmethod
    def _winner_payload(game, winner_user_id):
        if winner_user_id is None:
            return None
        winner = game.slot_for_user(winner_user_id)
        return {"username": winner.user.username, "color": winner.color.name}

    async def _send_player_results(
        self, game, rated_players, winner_user_id, winner_payload, reason
    ) -> None:
        for slot, rating in rated_players:
            await self._sender.safe_send(
                slot.websocket,
                {
                    "type": "game_result",
                    "game_id": game.game_id,
                    "outcome": self._outcome(slot.user.id, winner_user_id),
                    "reason": reason,
                    "rating": rating,
                    "winner": winner_payload,
                },
            )

    async def _send_spectator_results(
        self, room, game, winner_payload, reason
    ) -> None:
        for spectator in room.spectators():
            await self._sender.safe_send(
                spectator.websocket,
                {
                    "type": "game_result",
                    "game_id": game.game_id,
                    "outcome": "spectator",
                    "reason": reason,
                    "rating": spectator.user.rating,
                    "winner": winner_payload,
                },
            )
