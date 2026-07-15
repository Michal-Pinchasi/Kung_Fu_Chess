import sys, os
sys.path.insert(0, ".")
sys.path.insert(0, "view/ui")

from storage.board_parser import BoardParser
from engin.game_engine import GameEngine
from model.position import Position
from view.ui.layout.coordinate_mapper import CoordinateMapper
from view.ui.layout.layout import Layout

board = BoardParser.parse("""wR wN wB wQ wK wB wN wR
wP wP wP wP wP wP wP wP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
bP bP bP bP bP bP bP bP
bR bN bB bQ bK bB bN bR""")

engine = GameEngine(board)

print(f"Layout: BOARD_X={Layout.BOARD_X}, BOARD_Y={Layout.BOARD_Y}, BOARD_BORDER={Layout.BOARD_BORDER}, SQUARE_SIZE={Layout.SQUARE_SIZE}")
print()

# Simulate clicking on white pawn at row=1, col=0
px1, py1 = CoordinateMapper.cell_center_to_pixel(1, 0)
print(f"Click 1 - white pawn (1,0): pixel=({px1},{py1})")
engine.click_at_window_pixel(px1, py1)
print(f"  selected_cell = {engine.controller.selected_cell}")
print()

# Simulate clicking on destination row=2, col=0
px2, py2 = CoordinateMapper.cell_center_to_pixel(2, 0)
print(f"Click 2 - destination (2,0): pixel=({px2},{py2})")
result = None
original_request = engine.request_move
def patched_request(src, dst):
    global result
    result = original_request(src, dst)
    print(f"  request_move({src}, {dst}) -> accepted={result.is_accepted}, reason={result.reason}")
    return result
engine.request_move = patched_request

engine.click_at_window_pixel(px2, py2)
print(f"  selected_cell after = {engine.controller.selected_cell}")
print(f"  active_moves count = {len(engine.arbiter.pending)}")
