import pytest
from model.piece import Piece
from model.constants import PieceKind, PieceColor
from model.score import Score


def _piece(kind: PieceKind, color: PieceColor) -> Piece:
    return Piece(id=f"{color.value}{kind.value}_1", kind=kind, color=color)


def test_initial_scores_are_zero():
    score = Score()
    assert score.white_score == 0
    assert score.black_score == 0


@pytest.mark.parametrize("kind,points", [
    (PieceKind.PAWN, 1),
    (PieceKind.KNIGHT, 3),
    (PieceKind.BISHOP, 3),
    (PieceKind.ROOK, 5),
    (PieceKind.QUEEN, 9),
])
def test_white_credited_when_black_piece_captured(kind, points):
    score = Score()
    score.credit_capture(_piece(kind, PieceColor.BLACK))

    assert score.white_score == points
    assert score.black_score == 0


@pytest.mark.parametrize("kind,points", [
    (PieceKind.PAWN, 1),
    (PieceKind.KNIGHT, 3),
    (PieceKind.BISHOP, 3),
    (PieceKind.ROOK, 5),
    (PieceKind.QUEEN, 9),
])
def test_black_credited_when_white_piece_captured(kind, points):
    score = Score()
    score.credit_capture(_piece(kind, PieceColor.WHITE))

    assert score.black_score == points
    assert score.white_score == 0


def test_king_capture_awards_zero_points():
    score = Score()
    score.credit_capture(_piece(PieceKind.KING, PieceColor.BLACK))

    assert score.white_score == 0
    assert score.black_score == 0


def test_scores_accumulate_across_multiple_captures():
    score = Score()
    score.credit_capture(_piece(PieceKind.PAWN, PieceColor.BLACK))    # white +1
    score.credit_capture(_piece(PieceKind.ROOK, PieceColor.BLACK))    # white +5
    score.credit_capture(_piece(PieceKind.QUEEN, PieceColor.WHITE))   # black +9

    assert score.white_score == 6
    assert score.black_score == 9
