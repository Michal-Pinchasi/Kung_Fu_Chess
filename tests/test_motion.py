import pytest
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from realtime.motion import PendingMove, PendingJump, PendingRest


def test_pending_move_fields():
    """PendingMove stores piece, source, destination, and end time."""
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    frm = Position(0, 0)
    to = Position(0, 3)

    move = PendingMove(piece=piece, frm=frm, to=to, end_time_ms=3000)

    assert move.piece is piece
    assert move.frm == frm
    assert move.to == to
    assert move.end_time_ms == 3000


def test_pending_jump_fields():
    """PendingJump stores piece, position, and end time."""
    piece = Piece(id="bK_1", kind=PieceKind.KING, color=PieceColor.BLACK)
    pos = Position(2, 2)

    jump = PendingJump(piece=piece, pos=pos, end_time_ms=1000)

    assert jump.piece is piece
    assert jump.pos == pos
    assert jump.end_time_ms == 1000


def test_pending_move_distinct_from_pending_jump():
    """PendingMove and PendingJump are separate types."""
    piece = Piece(id="wN_1", kind=PieceKind.KNIGHT, color=PieceColor.WHITE)
    move = PendingMove(piece=piece, frm=Position(0, 0), to=Position(2, 1), end_time_ms=1000)
    jump = PendingJump(piece=piece, pos=Position(0, 0), end_time_ms=1000)

    assert not isinstance(move, PendingJump)
    assert not isinstance(jump, PendingMove)


def test_pending_rest_fields():
    """PendingRest stores piece and end time."""
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)

    rest = PendingRest(piece=piece, end_time_ms=2000)

    assert rest.piece is piece
    assert rest.end_time_ms == 2000
    assert not isinstance(rest, PendingMove)
    assert not isinstance(rest, PendingJump)
