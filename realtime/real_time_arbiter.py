from typing import List
from model.position import Position
from realtime.motion import Motion

class RealTimeArbiter:
    """
    בורר זמן האמת של המשחק.
    רכיב מכני טהור האחראי אך ורק על הרצת שעון התנועות וביצוען הפיזי על הלוח בנחיתה.
    """
    def __init__(self, board):
        self.board = board
        self.active_motions = [] 

    def has_motion_on_path(self, source: Position, destination: Position) -> bool:
        """בדיקה גיאומטרית יבשה: האם משבצות המקור או היעד תפוסות כרגע בתנועה באוויר"""
        for motion in self.active_motions:
            if (motion.source == source or 
                motion.destination == destination or 
                motion.destination == source or 
                motion.source == destination):
                return True
        return False

    def start_motion(self, piece, source: Position, destination: Position, duration_ticks: int = 10):
        """רישום מכני של תנועה חדשה באוויר"""
        motion = Motion(piece, source, destination, duration_ticks)
        self.active_motions.append(motion)

    def advance_time(self, ms: int):
        ticks_to_run = ms // 100
        for _ in range(ticks_to_run):
            for motion in list(self.active_motions):
                motion.tick()
                if motion.is_finished():
                    # הנחתה ישירה של הכלי שנמצא בתוך אובייקט התנועה
                    self.board.set_piece(motion.destination.row, motion.destination.col, motion.piece)
                    self.active_motions.remove(motion)