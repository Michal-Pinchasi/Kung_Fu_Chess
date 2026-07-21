"""Graphical WebSocket client for local two-player Kung Fu Chess."""

import argparse
import os
import sys

import cv2

# Some existing UI modules use legacy absolute imports such as ``graphics``.
# Include both this UI directory and the project root when launched with -m.
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from network.client.remote_engine import RemoteEngine
from network.client.remote_game_client import RemoteGameClient
from view.ui.app import ASSETS_DIR
from view.ui.config.ui_config_loader import FPS, WINDOW_TITLE
from view.ui.input.mouse_handler import MouseHandler
from view.ui.rendering.board_renderer import BoardRenderer
from view.ui.rendering.move_history_renderer import MoveHistoryRenderer
from view.ui.rendering.overlay_renderer import OverlayRenderer
from view.ui.rendering.piece_renderer import PieceRenderer
from view.ui.scene.game_scene import GameScene
from view.ui.window.game_canvas import GameCanvas


def app(uri: str = "ws://localhost:8765", window_name: str | None = None) -> None:
    client = RemoteGameClient(uri)
    client.connect()
    if not client.wait_until_ready():
        raise RuntimeError(client.error or "Timed out connecting to server.")
    if client.error:
        raise RuntimeError(client.error)

    engine = RemoteEngine(client)
    canvas = GameCanvas(os.path.join(ASSETS_DIR, "back_graound.jpg"))
    scene = GameScene(canvas, BoardRenderer(os.path.join(ASSETS_DIR, "board.jpg")),
                      PieceRenderer(os.path.join(ASSETS_DIR, "pieces2")), OverlayRenderer(), engine,
                      MoveHistoryRenderer())
    title = window_name or f"{WINDOW_TITLE} - {'White' if client.color == 'w' else 'Black'}"
    first_frame = scene.render()
    height, width = first_frame.img.shape[:2]
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, width, height)
    cv2.imshow(title, first_frame.img)
    MouseHandler(engine.controller).register(title)

    try:
        while True:
            cv2.imshow(title, scene.render().img)
            key = cv2.waitKey(1000 // FPS) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        client.close()
        cv2.destroyWindow(title)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kung Fu Chess network client")
    parser.add_argument("--uri", default="ws://localhost:8765")
    parser.add_argument("--window-name")
    args = parser.parse_args()
    app(args.uri, args.window_name)
