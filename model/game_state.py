from model.board import Board
from typing import List
class GameState:
    def __init__(self, board: Board):
        self.board = board
        self.is_game_over = False
        self.winner = None

class MoveResult:
    """אובייקט התשובה הרשמי של ה-GameEngine"""
    def __init__(self, is_accepted: bool, reason: str):
        self.is_accepted = is_accepted  
        self.reason = reason            

class PieceSnapshot:
    def __init__(self, id: str, kind: str, color: str, x: float, y: float, state: str):
        self.id = id
        self.kind = kind
        self.color = color
        self.x = x          
        self.y = y          
        self.state = state  # idle / moving / captured

class GameSnapshot:
    def __init__(self, board_width: int, board_height: int, pieces: List[PieceSnapshot], selected_cell, game_over: bool):
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces               
        self.selected_cell = selected_cell 
        self.game_over = game_over