from model.position import Position

class PendingMove:
    """מייצג תנועה קווית רגילה שנמצאת בתהליך"""
    def __init__(self, piece, frm: Position, to: Position, end_time_ms: int):
        self.piece = piece
        self.frm = frm
        self.to = to
        self.end_time_ms = end_time_ms

class PendingJump:
    """מייצג קפיצה הגנתית במקום שנמצאת בתהליך"""
    def __init__(self, piece, pos: Position, end_time_ms: int):
        self.piece = piece
        self.pos = pos
        self.end_time_ms = end_time_ms

class Jumping:
    """אובייקט הסטטוס של משבצת שמתבצעת בה קפיצה"""
    def __init__(self, jump: PendingJump):
        self.jump = jump