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
from network.client.connection_state import ConnectionState
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
    canvas = GameCanvas(os.path.join(ASSETS_DIR, "back_graound.jpg"))
    title = window_name or f"{WINDOW_TITLE} - Login"
    first_frame = canvas.fresh_frame()
    height, width = first_frame.img.shape[:2]
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, width, height)

    if not _login_screen(client, canvas, title):
        client.close()
        cv2.destroyWindow(title)
        return

    if not _matchmaking_screen(client, canvas, title):
        client.close()
        cv2.destroyWindow(title)
        return

    engine = RemoteEngine(client)
    scene = GameScene(canvas, BoardRenderer(os.path.join(ASSETS_DIR, "board.jpg")),
                      PieceRenderer(os.path.join(ASSETS_DIR, "pieces2")), OverlayRenderer(), engine,
                      MoveHistoryRenderer())
    first_frame = scene.render()
    cv2.imshow(title, first_frame.img)
    MouseHandler(engine.controller).register(title)

    try:
        while True:
            frame = scene.render()
            _draw_account_status(frame, client)
            _draw_network_status(frame, client)
            _draw_game_over_result(frame, client)
            cv2.imshow(title, frame.img)
            key = cv2.waitKey(1000 // FPS) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        client.close()
        cv2.destroyWindow(title)


def _login_screen(client: RemoteGameClient, canvas: GameCanvas, title: str) -> bool:
    """A keyboard-driven graphical login/register screen inside the game window."""
    username, password, active_field = "", "", 0
    register_mode, submitted = False, False
    while True:
        frame = canvas.fresh_frame()
        frame.draw_rect(260, 180, 780, 550, color=(20, 20, 20, 255), alpha=0.88)
        frame.put_text("KUNG FU CHESS", 450, 270, 1.4, color=(40, 215, 255, 255), thickness=3)
        frame.put_text("Create account" if register_mode else "Sign in", 560, 325, 1.0, thickness=2)
        _field(frame, "Username", username, 430, 380, active_field == 0)
        _field(frame, "Password", "*" * len(password), 430, 490, active_field == 1)
        action = "REGISTER" if register_mode else "LOGIN"
        frame.put_text(f"ENTER: {action}   TAB: next field   R: switch mode   ESC: exit", 355, 640, 0.55)
        if submitted:
            status = client.error or "Connecting..."
            color = (0, 0, 255, 255) if client.error else (0, 220, 255, 255)
            frame.put_text(status, 430, 585, 0.65, color=color, thickness=2)
        cv2.imshow(title, frame.img)
        key = cv2.waitKey(1000 // FPS) & 0xFF
        if key in (27, ord("q")):
            return False
        if client.username is not None and client.state == ConnectionState.LOBBY:
            return True
        if key == 9:
            active_field = 1 - active_field
        elif key in (ord("r"), ord("R")):
            register_mode, submitted, client.error = not register_mode, False, None
        elif key in (8, 127):
            if active_field == 0:
                username = username[:-1]
            else:
                password = password[:-1]
        elif key in (10, 13):
            if username and password:
                submitted = True
                client.authenticate(username, password, register_mode)
        elif 32 <= key <= 126:
            if active_field == 0:
                username += chr(key)
            else:
                password += chr(key)


def _field(frame, label: str, value: str, x: int, y: int, active: bool) -> None:
    frame.put_text(label, x, y, 0.65)
    frame.draw_rect(x, y + 15, 450, 55, color=(255, 255, 255, 255), thickness=2 if active else 1)
    frame.put_text(value, x + 12, y + 52, 0.8, color=(255, 255, 255, 255), thickness=2)


def _matchmaking_screen(client: RemoteGameClient, canvas: GameCanvas, title: str) -> bool:
    """Lobby and queue presentation; network state remains owned by the client."""
    while True:
        frame = canvas.fresh_frame()
        frame.draw_rect(280, 190, 740, 430, color=(20, 20, 20, 255), alpha=0.88)
        frame.put_text(f"Welcome {client.username}", 450, 285, 1.0,
                       color=(40, 215, 255, 255), thickness=2)
        frame.put_text(f"ELO: {client.rating}", 560, 345, 0.8, thickness=2)
        searching = client.state == ConnectionState.SEARCHING
        instruction = "ENTER: CANCEL SEARCH" if searching else "ENTER: PLAY"
        frame.put_text(client.notification or "Ready to play", 450, 430, 0.75, thickness=2)
        frame.put_text(instruction, 475, 510, 0.72, thickness=2)
        frame.put_text("ESC: exit", 570, 565, 0.55)
        cv2.imshow(title, frame.img)
        key = cv2.waitKey(1000 // FPS) & 0xFF
        if client.state == ConnectionState.PLAYING:
            return True
        if key in (27, ord("q")):
            return False
        if key in (10, 13):
            client.leave_queue() if searching else client.join_queue()


def _draw_account_status(frame, client: RemoteGameClient) -> None:
    """Keep the authenticated identity and persisted rating visible in-game."""
    color_name = "WHITE" if client.color == "w" else "BLACK"
    frame.draw_rect(20, 20, 315, 75, color=(20, 20, 20, 255), alpha=0.75)
    frame.put_text(f"{client.username} | {color_name} | ELO {client.rating}", 35, 65, 0.58,
                   color=(255, 255, 255, 255), thickness=2)
    if client.game_result:
        outcome = client.game_result["outcome"].upper()
        frame.put_text(f"RESULT: {outcome} | NEW ELO: {client.rating}", 385, 85, 0.75,
                       color=(40, 215, 255, 255), thickness=2)


def _draw_network_status(frame, client: RemoteGameClient) -> None:
    if client.state == ConnectionState.RECONNECTING:
        frame.draw_rect(360, 340, 610, 130, color=(10, 10, 10, 255), alpha=0.9)
        frame.put_text("CONNECTION LOST - RECONNECTING...", 410, 415, 0.8,
                       color=(0, 180, 255, 255), thickness=2)
    if client.opponent_disconnect_seconds is not None:
        frame.draw_rect(365, 330, 600, 150, color=(10, 10, 10, 255), alpha=0.9)
        frame.put_text("OPPONENT DISCONNECTED", 440, 395, 0.85,
                       color=(0, 180, 255, 255), thickness=2)
        frame.put_text(f"Technical win in {client.opponent_disconnect_seconds}s", 460, 445, 0.72,
                       thickness=2)


def _draw_game_over_result(frame, client: RemoteGameClient) -> None:
    """Draw the authoritative winner identity supplied by the server result."""
    if not client.game_result:
        return
    outcome = client.game_result["outcome"]
    if outcome == "draw":
        winner_text = "DRAW"
    elif outcome == "win":
        winner_text = f"{client.username} | {'WHITE' if client.color == 'w' else 'BLACK'} | WIINN"
    else:
        opponent = client.opponent or {"username": "OPPONENT"}
        opponent_color = "BLACK" if client.color == "w" else "WHITE"
        winner_text = f"{opponent['username']} | {opponent_color} | WIINN"

    frame.draw_rect(320, 315, 720, 190, color=(10, 10, 10, 255), alpha=0.92)
    frame.put_text("GAME OVER", 500, 385, 1.25,
                   color=(40, 215, 255, 255), thickness=3)
    frame.put_text(winner_text, 385, 455, 0.82,
                   color=(255, 255, 255, 255), thickness=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kung Fu Chess network client")
    parser.add_argument("--uri", default="ws://localhost:8765")
    parser.add_argument("--window-name")
    args = parser.parse_args()
    app(args.uri, args.window_name)
