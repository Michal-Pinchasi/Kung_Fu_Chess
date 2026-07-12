from model.position import Position
from model.game_state import GameState, GameSnapshot, MoveResult
from Kung_Fu_Chess.rules.rule_engine import RuleEngine
from Kung_Fu_Chess.realtime.real_time_arbiter import RealTimeArbiter

class GameEngine:
    """
    המנהל והמתאם הראשי של האפליקציה (Orchestrator).
    משמש כגבול הפקודות הציבורי עבור ה-Controller וה-TextTestRunner.
    """
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        # יצירת בורר זמן האמת המשויך ללוח של המשחק
        self.arbiter = RealTimeArbiter(self.game_state.board)

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """
        הפקודה הציבורית הראשית לקבלת בקשת מהלך.
        מיישמת את תנאי ההגנה ברמת האפליקציה לפני הפנייה לחוקים.
        """
        # 1. דחיית מהלך כאשר game_over הוא true
        if self.game_state.is_game_over:
            return MoveResult(is_accepted=False, reason="game_over")

        # 2. דחיית מהלך כאשר במסלול המשותף כבר יש תנועה פעילה
        if self.arbiter.has_motion_on_path(source, destination):
            return MoveResult(is_accepted=False, reason="motion_in_progress")

        # 3. קריאה ל-RuleEngine.validate_move רק לאחר שתנאי ההגנה עוברים
        validation = RuleEngine.validate_move(self.game_state.board, source, destination)
        if not validation.is_valid:
            # סיבות לא-חוקיות ברמת הכלל מועתקות מ-MoveValidation
            return MoveResult(is_accepted=False, reason=validation.reason)

        # 4. התחלת תנועה חוקית דרך RealTimeArbiter
        piece = self.game_state.board.get_piece(source.row, source.col)
        self.arbiter.start_motion(piece, source, destination)
        
        # עבור פקודה חוקית שהתקבלה, reason הוא "ok"
        return MoveResult(is_accepted=True, reason="ok")

    def wait(self, ms: int):
        """האצלת wait(ms) אל RealTimeArbiter.advance_time(ms)"""
        # קידום הזמן המדומה וקבלת התראת אכילת מלך במידה וקמרה
        king_captured = self.arbiter.advance_time(ms)
        
        # קבלת התראת אכילת מלך מפתרון ההגעה והגדרת game_over
        if king_captured:
            self.game_state.is_game_over = True
            # (באיטרציות הבאות נוכל לחלץ בצורה מדויקת יותר מי המנצח על בסיס הצבע שנשאר)

    def get_snapshot(self) -> GameSnapshot:
        """יצירת GameSnapshot לקריאה-בלבד עבור ה-renderer וה-BoardPrinter"""
        return GameSnapshot(
            board=self.game_state.board,
            is_game_over=self.game_state.is_game_over,
            winner=self.game_state.winner
        )