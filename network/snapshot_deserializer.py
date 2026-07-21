"""Rebuild renderer-friendly snapshots received from the WebSocket server."""

from model.game_state import GameSnapshot, PieceSnapshot
from model.move_history import Move, MoveHistory
from model.position import Position
from model.score import Score


def deserialize(data: dict) -> GameSnapshot:
    """Convert the JSON-compatible snapshot payload sent by ``serialize``."""
    pieces = [PieceSnapshot(**piece) for piece in data["pieces"]]
    history = _deserialize_history(data.get("move_history"))
    score = _deserialize_score(data.get("score"))
    return GameSnapshot(
        board_width=data["board_width"],
        board_height=data["board_height"],
        pieces=pieces,
        selected_cell=_position(data.get("selected_cell")),
        game_over=data["game_over"],
        move_history=history,
        score=score,
    )


def _position(data):
    return None if data is None else Position(data["row"], data["col"])


def _deserialize_history(data):
    if data is None:
        return None
    history = MoveHistory()
    history.white_moves = [_move(item) for item in data["white"]]
    history.black_moves = [_move(item) for item in data["black"]]
    return history


def _move(data):
    return Move(_position(data["source"]), _position(data["destination"]),
                data["piece_kind"], data["is_capture"])


def _deserialize_score(data):
    if data is None:
        return None
    score = Score()
    score.white_score = data["white"]
    score.black_score = data["black"]
    return score
