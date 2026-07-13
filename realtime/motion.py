from model.position import Position


class PendingMove:
    """Represents a linear move that is currently in progress."""

    def __init__(self, piece, frm: Position, to: Position, end_time_ms: int):
        self.piece = piece
        self.frm = frm
        self.to = to
        self.end_time_ms = end_time_ms


class PendingJump:
    """Represents a defensive jump in place that is currently in progress."""

    def __init__(self, piece, pos: Position, end_time_ms: int):
        self.piece = piece
        self.pos = pos
        self.end_time_ms = end_time_ms


class Jumping:
    """Status marker for a cell that currently has an active jump."""

    def __init__(self, jump: PendingJump):
        self.jump = jump
