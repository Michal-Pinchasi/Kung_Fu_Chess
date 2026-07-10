from model.board import Board

class GameState:
    def __init__(self, board: Board):
        self.board = board
        self.is_game_over = False
        self.winner = None

class GameSnapshot:
    """ייצוג לקריאה-בלבד של מצב המשחק שנחשף ל-renderer"""
    def __init__(self, board: Board, is_game_over: bool, winner: str):
        self.board = board
        self.is_game_over = is_game_over
        self.winner = winner

class MoveResult:
    """אובייקט התשובה הרשמי של ה-GameEngine"""
    def __init__(self, is_accepted: bool, reason: str):
        self.is_accepted = is_accepted  # האם הפקודה התקבלה
        self.reason = reason            # "ok", "game_over", "motion_in_progress", או שגיאת כלל