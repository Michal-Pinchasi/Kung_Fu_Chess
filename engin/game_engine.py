import sys
from model.position import Position
from model.game_state import GameState, MoveResult
from rules.rule_engine import RuleEngine
from realtime.real_time_arbiter import RealTimeArbiter

class GameEngine:
    """
    המנהל והמתאם הראשי של האפליקציה (Orchestrator)[cite: 6].
    משמש כגבול הפקודות הציבורי עבור ה-Controller והממשק הויזואלי.
    """
    def __init__(self, board):
        self.board = board
        self.game_state = GameState(self.board)
        self.arbiter = RealTimeArbiter(self.board)

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """הפקודה הציבורית הראשית לקבלת בקשת מהלך[cite: 6]"""
        if self.game_state.is_game_over:
            return MoveResult(is_accepted=False, reason="game_over")

        if self.arbiter.has_motion_on_path(source, destination):
            return MoveResult(is_accepted=False, reason="motion_in_progress")

        # קריאה לאימות חוקים[cite: 6]
        validation = RuleEngine.validate_move(self.board, source, destination)
        if not validation.is_valid:
            return MoveResult(is_accepted=False, reason=validation.reason)

        piece = self.board.get_piece(source.row, source.col)
        
        # עדכון מצב הכלי לסטטוס זז[cite: 4]
        if piece and piece != ".":
            piece.state = "moving"

        # התחלת תנועה חוקית דרך RealTimeArbiter[cite: 6]
        self.arbiter.start_motion(piece, source, destination)
        return MoveResult(is_accepted=True, reason="ok")

    def wait(self, ms: int):
        """האצלת קידום הזמן ותשאול ה-RuleEngine לגבי מצב המשחק[cite: 6]"""
        # 1. קידום הזמן המכני
        self.arbiter.advance_time(ms)
        
        # 2. תשאול מנוע החוקים הסטטי (SRP מושלם ללא סריקה מקומית)
        winner = RuleEngine.get_game_winner(self.board)
        if winner:
            self.game_state.is_game_over = True
            self.game_state.winner = winner

    def get_snapshot(self):
        """יצירת GameSnapshot לקריאה-בלבד[cite: 6]"""
        return self.game_state