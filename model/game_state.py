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
class PieceSnapshot:
    def __init__(self, id: str, kind: str, color: str, x: float, y: float, state: str):
        self.id = id
        self.kind = kind
        self.color = color
        self.x = x          # מיקום פיקסלי אמיתי על המסך (לצורך האנימציה)
        self.y = y          # מיקום פיקסלי אמיתי על המסך
        self.state = state  # idle / moving / captured

class GameSnapshot:
    def __init__(self, board_width: int, board_height: int, pieces: list[PieceSnapshot], selected_cell, game_over: bool):
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces               # רשימת הכלים במצבם הנוכחי
        self.selected_cell = selected_cell # ה-Position שנבחר כרגע בבקר (אם יש)
        self.game_over = game_over