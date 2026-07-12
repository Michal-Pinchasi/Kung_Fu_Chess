import pytest
from model.position import Position
from model.piece import Piece
from model.constants import PieceColor, PieceKind
from realtime.motion import Motion

def test_motion_lifecycle_ticks():
    # תוקן סדר הפרמטרים: id, kind, color
    piece = Piece(id="wR_1", kind=PieceKind.ROOK, color=PieceColor.WHITE)
    source = Position(0, 0)
    destination = Position(0, 3)
    
    motion = Motion(piece, source, destination, duration_ticks=2)
    
    assert motion.is_finished() is False
    assert motion.remaining_ticks == 2
    
    motion.tick()
    assert motion.is_finished() is False
    assert motion.remaining_ticks == 1
    
    motion.tick()
    assert motion.is_finished() is True
    assert motion.remaining_ticks == 0