"""
Visual integration tests for Kung Fu Chess UI.

test_visual_all_states  — static snapshots (3 states, press key to advance)
test_visual_game        — animated game demo: pieces move in real time

Run:
    python -m pytest tests/test_visual.py::test_visual_all_states -v -s
    python -m pytest tests/test_visual.py::test_visual_game        -v -s
"""

import os, sys, time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_UI   = os.path.join(_ROOT, "view", "ui")
for p in (_ROOT, _UI):
    if p not in sys.path:
        sys.path.insert(0, p)

import cv2

_ASSETS = os.path.join(_UI, "assets")
_BG     = os.path.join(_ASSETS, "back_graound.jpg")
_BRD    = os.path.join(_ASSETS, "board.jpg")
_PIECES = os.path.join(_ASSETS, "pieces2")          # ← skin 2

_WINDOW = "Kung Fu Chess"

_FULL_BOARD = """\
wR wN wB wQ wK wB wN wR
wP wP wP wP wP wP wP wP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
bP bP bP bP bP bP bP bP
bR bN bB bQ bK bB bN bR"""


# ── helpers ────────────────────────────────────────────────────────────────

def _build_scene(board_text: str):
    from storage.board_parser import BoardParser
    from engin.game_engine import GameEngine
    from view.ui.window.game_canvas import GameCanvas
    from view.ui.rendering.board_renderer import BoardRenderer
    from view.ui.rendering.piece_renderer import PieceRenderer
    from view.ui.rendering.overlay_renderer import OverlayRenderer
    from view.ui.scene.game_scene import GameScene

    board  = BoardParser.parse(board_text)
    engine = GameEngine(board)
    scene  = GameScene(
        canvas           = GameCanvas(_BG),
        board_renderer   = BoardRenderer(_BRD),
        piece_renderer   = PieceRenderer(_PIECES),
        overlay_renderer = OverlayRenderer(),
        engine           = engine,
    )
    return scene, engine


def _show_frame(frame, label: str = "") -> None:
    """Show one frame and wait for a key press."""
    if label:
        frame.put_text(label, 20, 40, 0.8,
                       color=(255, 255, 255, 255), thickness=2)
    cv2.namedWindow(_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(_WINDOW, frame.img.shape[1], frame.img.shape[0])
    cv2.imshow(_WINDOW, frame.img)
    cv2.waitKey(0)


def _show_frame_timed(frame, ms: int) -> bool:
    """Show one frame for ms milliseconds. Returns False if Q/Esc pressed."""
    cv2.namedWindow(_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(_WINDOW, frame.img.shape[1], frame.img.shape[0])
    cv2.imshow(_WINDOW, frame.img)
    key = cv2.waitKey(ms) & 0xFF
    return key not in (ord('q'), 27)


# ── Test 1: static states ──────────────────────────────────────────────────

def test_visual_all_states():
    """Three static snapshots in one window. Press any key to advance."""
    from model.position import Position

    # State 1 – full starting board
    scene, _ = _build_scene(_FULL_BOARD)
    _show_frame(scene.render(), "State 1: Starting board  [press any key]")

    # State 2 – white king selected
    scene2, engine2 = _build_scene(_FULL_BOARD)
    engine2.controller.selected_cell = Position(0, 4)
    _show_frame(scene2.render(), "State 2: White king selected  [press any key]")

    # State 3 – game over
    scene3, engine3 = _build_scene(_FULL_BOARD)
    engine3.game_state.is_game_over = True
    engine3.game_state.winner = "WHITE"
    _show_frame(scene3.render(), "State 3: GAME OVER – WHITE WINS  [press any key]")

    cv2.destroyAllWindows()


# ── Test 2: animated game demo ─────────────────────────────────────────────

def test_visual_game():
    """
    Animated demo: a sequence of real moves is executed and the board
    redraws at ~30 FPS so you can watch pieces travel to their destinations.

    Press Q or Esc to exit early.
    """
    scene, engine = _build_scene(_FULL_BOARD)

    # Sequence of (from_pixel_x, from_pixel_y, to_pixel_x, to_pixel_y)
    # These are engine.controller.click() calls — let the controller/engine
    # decide legality exactly as a real user would.
    # Coordinates are pixel positions of cell centres using CELL_SIZE=100.
    CELL = 100   # BoardMapper.CELL_SIZE

    def click(row, col):
        """Simulate a click at the centre of cell (row, col) via the controller."""
        px = col * CELL + CELL // 2
        py = row * CELL + CELL // 2
        engine.controller.click(px, py)

    # Pre-planned sequence of moves: (src_row, src_col, dst_row, dst_col)
    moves = [
        # White pawn e2→e3
        (1, 4, 2, 4),
        # Black pawn e7→e6
        (6, 4, 5, 4),
        # White knight g1→f3
        (0, 6, 2, 5),
        # Black knight g8→f6
        (7, 6, 5, 5),
        # White bishop f1→c4
        (0, 5, 3, 2),
        # Black bishop f8→c5
        (7, 5, 4, 2),
        # White queen d1→h5
        (0, 3, 4, 7),
    ]

    FPS_MS      = 33     # ~30 fps render interval
    WAIT_MS     = 2500   # wait between issuing moves
    MAX_RUNTIME = 60     # auto-close after 60 seconds

    move_index = 0
    last_move_time = time.time()
    start_time = time.time()
    running = True

    while running:
        # Auto-close after MAX_RUNTIME seconds
        if time.time() - start_time > MAX_RUNTIME:
            running = False
            continue

        # Issue the next move when the timer fires
        now = time.time()
        if move_index < len(moves) and (now - last_move_time) * 1000 > WAIT_MS:
            src_r, src_c, dst_r, dst_c = moves[move_index]
            click(src_r, src_c)   # first click  – select
            click(dst_r, dst_c)   # second click – move request
            move_index += 1
            last_move_time = now

        # Advance engine time by one frame
        engine.wait(FPS_MS)

        # Render and display
        frame = scene.render()
        frame.put_text(
            f"Move {move_index}/{len(moves)}  (Q=quit)",
            20, 40, 0.7, color=(255, 255, 0, 255), thickness=2,
        )
        running = _show_frame_timed(frame, FPS_MS)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    # When run directly: python tests/test_visual.py
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true", help="Run static states test")
    args = parser.parse_args()
    if args.static:
        test_visual_all_states()
    else:
        test_visual_game()
