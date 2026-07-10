from model.position import Position
from realtime.motion import Motion

class RealTimeArbiter:
    """
    בורר זמן האמת של המשחק.
    אחראי על ניהול התנועות הפעילות באוויר ופתרון הגעתן ללוח.
    """
    def __init__(self, board):
        self.board = board
        self.active_motions: list[Motion] = []  # רשימת התנועות שנמצאות כרגע באוויר

    def has_motion_on_path(self, source: Position, destination: Position) -> bool:
        """
        בודק האם קיימת כבר תנועה פעילה באוויר שמשתמשת במשבצת המקור או היעד.
        מונע משחקן לשלוח פקודה נוספת עבור כלי שכבר נמצא בתנועה.
        """
        for motion in self.active_motions:
            # אם כלי המקור או היעד מעורבים בתנועה קיימת כלשהי
            if (motion.source == source or 
                motion.destination == destination or 
                motion.destination == source or 
                motion.source == destination):
                return True
        return False

    def start_motion(self, piece, source: Position, destination: Position, duration_ticks: int = 10):
        """
        רושם תנועה חדשה בזמן אמת ומעביר את מצב הכלי ל-moving.
        """
        motion = Motion(piece, source, destination, duration_ticks)
        self.active_motions.append(motion)
        
        # עדכון מצב הכלי לסטטוס זז (כדי שהרנדרר ידע לא לצייר אותו במשבצת המקור)
        if piece and piece != ".":
            piece.state = "moving"

    def advance_time(self, ms: int) -> bool:
        """
        מריץ את הזמן המדומה קדימה לפי מילישניות ומעדכן את ה-Ticks של כל התנועות.
        אם תנועה מסתיימת, היא מבוצעת פיזית על הלוח.
        מחזיר True במידה וזוהתה אכילת מלך ברגע ההגעה (King Capture Alert).
        """
        king_captured = False
        # הגדרת פקטור המרה: נניח שכל 100ms מייצגים פעימת זמן אחת (1 Tick)
        ticks_to_run = ms // 100
        
        for _ in range(ticks_to_run):
            # לולאה על עותק של הרשימה כדי לאפשר הסרת איברים תוך כדי ריצה בצורה בטוחה
            for motion in list(self.active_motions):
                motion.tick()
                
                # בדיקה האם הכלי הגיע לרגע ההכרעה שלו (סיום זמן התנועה)
                if motion.is_finished():
                    # 1. בדיקת הגנה (שומר סף אחרון בזמן אמת): האם כלי ידידותי נכנס ליעד בזמן שהיינו באוויר?
                    current_target = self.board.get_piece(motion.destination.row, motion.destination.col)
                    if current_target != "." and current_target.color == motion.piece.color:
                        # המהלך מבוטל! נחזיר את הכלי המקורי למצב מנוחה בלי להזיז אותו
                        motion.piece.state = "idle"
                        self.active_motions.remove(motion)
                        continue

                    # 2. זיהוי אכילת מלך (התראת אכילת מלך עבור ה-GameEngine)
                    if current_target != "." and current_target.kind.value == "K":
                        king_captured = True

                    # 3. ביצוע ההזזה הפיזית על גבי הלוח ודריסת היעד
                    self.board.move_piece(motion.source, motion.destination)
                    
                    # 4. החזרת סטטוס הכלי למצב מנוחה (idle) לאחר שהגיע בהצלחה
                    motion.piece.state = "idle"
                    
                    # הסרת התנועה מרשימת התנועות הפעילות באוויר
                    self.active_motions.remove(motion)
                    
        return king_captured