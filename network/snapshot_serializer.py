"""
Converts a GameSnapshot (and its nested PieceSnapshot/MoveHistory/Score
objects) into plain, JSON-serializable dicts for broadcast to WebSocket
clients.

Keeps this JSON-shaping concern out of GameServer (which shouldn't need to
know GameSnapshot's internal field layout) and out of model/ (which
shouldn't need to know JSON, or networking, exists at all).
"""

from typing import Optional
from model.game_state import GameSnapshot, PieceSnapshot
from model.position import Position


def serialize(snapshot: GameSnapshot) -> dict:
    """Return a JSON-serializable dict representing the full game snapshot."""
    return {
        "board_width": snapshot.board_width,
        "board_height": snapshot.board_height,
        "pieces": [_serialize_piece(piece) for piece in snapshot.pieces],
        "selected_cell": _serialize_position(snapshot.selected_cell),
        "game_over": snapshot.game_over,
        "move_history": _serialize_move_history(snapshot.move_history),
        "score": _serialize_score(snapshot.score),
    }


def _serialize_piece(piece: PieceSnapshot) -> dict:
    """Return a JSON-serializable dict for a single PieceSnapshot."""
    return {
        "id": piece.id,
        "kind": piece.kind,
        "color": piece.color,
        "x": piece.x,
        "y": piece.y,
        "state": piece.state,
        "elapsed_state_ms": piece.elapsed_state_ms,
    }


def _serialize_position(position: Optional[Position]) -> Optional[dict]:
    """Return {"row": ..., "col": ...} for a Position, or None."""
    if position is None:
        return None
    return {"row": position.row, "col": position.col}


def _serialize_move_history(move_history) -> Optional[dict]:
    """Return {"white": [...], "black": [...]} of serialized moves, or None."""
    if move_history is None:
        return None
    return {
        "white": [_serialize_move(move) for move in move_history.get_white_moves()],
        "black": [_serialize_move(move) for move in move_history.get_black_moves()],
    }


def _serialize_move(move) -> dict:
    """Return a JSON-serializable dict for a single recorded Move."""
    return {
        "source": _serialize_position(move.source),
        "destination": _serialize_position(move.destination),
        "piece_kind": move.piece_kind,
        "is_capture": move.is_capture,
    }


def _serialize_score(score) -> Optional[dict]:
    """Return {"white": ..., "black": ...} of accumulated points, or None."""
    if score is None:
        return None
    return {"white": score.white_score, "black": score.black_score}
