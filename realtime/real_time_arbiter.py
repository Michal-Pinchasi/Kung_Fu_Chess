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

    def start_motion(self, piece, source: Position, destination: Position, duration_ticks: int = None):
        """רישום מכני של תנועה חדשה באוויר - תומך בקבלת זמן ידני מהטסטים"""
        if duration_ticks is None:
            distance = max(
                abs(destination.row - source.row),
                abs(destination.col - source.col)
            )
            duration_ticks = distance * 10

        motion = Motion(piece, source, destination, duration_ticks)
        self.active_motions.append(motion)

    def advance_time(self, ms: int) -> List:
        """מקדמת את הזמן ומחזירה רשימה של כלים שנאכלו (Arrival/Capture Events)"""
        ticks_to_run = ms // 100
        captured_pieces = []

        for _ in range(ticks_to_run):
            for motion in list(self.active_motions):
                motion.tick()

                if motion.is_finished():
                    # הסרת הכלי מהמקור
                    self.board.remove_piece(motion.source.row, motion.source.col)

                    # בדיקה האם יש כלי ביעד שעומד להיאכל
                    target_piece = self.board.get_piece(motion.destination.row, motion.destination.col)
                    if target_piece is not None:
                        captured_pieces.append(target_piece)
                        self.board.remove_piece(motion.destination.row, motion.destination.col)

                    # האצלת האחריות החוקתית ל-RuleEngine לפני הנחת הכלי סופית על הלוח
                    from rules.rule_engine import RuleEngine
                    RuleEngine.apply_post_arrival_rules(self.board, motion.piece, motion.destination)

                    # הנחת הכלי ביעד
                    self.board.set_piece(
                        motion.destination.row,
                        motion.destination.col,
                        motion.piece,
                    )

                    self.active_motions.remove(motion)
                    
        return captured_pieces