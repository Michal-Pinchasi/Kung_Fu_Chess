from model.position import Position

class Motion:
    """
    מייצג אובייקט נתונים של תנועה בודדת שנמצאת כרגע "באוויר" בזמן אמת.
    מנהל את השעון הפנימי של המהלך עד להגעתו ליעד.
    """
    def __init__(self, piece, source: Position, destination: Position, duration_ticks: int):
        self.piece = piece                  # אובייקט הכלי שזז כרגע
        self.source = source                # משבצת המקור שממנה הוא יצא
        self.destination = destination      # משבצת היעד אליה הוא אמור להגיע
        self.remaining_ticks = duration_ticks  # כמה פעימות זמן (Ticks) נשארו לו עד להגעה

    def tick(self):
        """מוריד פעימת זמן אחת מהתנועה בכל פעם שהזמן הכללי מתקדם"""
        if self.remaining_ticks > 0:
            self.remaining_ticks -= 1

    def is_finished(self) -> bool:
        """מחזיר True אם הכלי סיים את זמן התנועה שלו והגיע לרגע ההכרעה"""
        return self.remaining_ticks <= 0