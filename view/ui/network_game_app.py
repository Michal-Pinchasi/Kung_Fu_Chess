"""Application coordinator for the graphical network client."""

import os

import cv2

from network.client.connection_state import ConnectionState
from network.client.remote_engine import RemoteEngine
from network.client.remote_game_client import RemoteGameClient
from view.ui.app import ASSETS_DIR
from view.ui.config.ui_config_loader import FPS, WINDOW_TITLE
from view.ui.input.key_bindings import KeyBindings
from view.ui.input.mouse_handler import MouseHandler
from view.ui.presenters.game_result_presenter import GameResultPresenter
from view.ui.rendering.account_status_renderer import AccountStatusRenderer
from view.ui.rendering.board_renderer import BoardRenderer
from view.ui.rendering.move_history_renderer import MoveHistoryRenderer
from view.ui.rendering.network_status_renderer import NetworkStatusRenderer
from view.ui.rendering.overlay_renderer import OverlayRenderer
from view.ui.rendering.piece_renderer import PieceRenderer
from view.ui.rendering.room_screen_renderer import RoomScreenRenderer
from view.ui.scene.game_scene import GameScene
from view.ui.screens.lobby_screen import LobbyScreen
from view.ui.screens.login_screen import LoginScreen
from view.ui.window.game_canvas import GameCanvas


class NetworkGameApp:
    """Coordinates screen transitions and the lifetime of UI resources."""

    def __init__(self, uri, window_name, settings):
        self._settings = settings
        self._client = RemoteGameClient(uri)
        self._canvas = GameCanvas(self._asset(settings.background_asset))
        self._title = window_name or f"{WINDOW_TITLE} - Login"

    def run(self) -> None:
        self._client.connect()
        self._open_window()
        try:
            if not LoginScreen(
                self._client, self._canvas, self._title, self._settings
            ).run():
                return
            if self._client.state == ConnectionState.LOBBY:
                if not LobbyScreen(
                    self._client,
                    self._canvas,
                    self._title,
                    RoomScreenRenderer(),
                ).run():
                    return
            self._run_game()
        finally:
            self._client.close()
            cv2.destroyWindow(self._title)

    def _open_window(self) -> None:
        height, width = self._canvas.fresh_frame().img.shape[:2]
        cv2.namedWindow(self._title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._title, width, height)

    def _run_game(self) -> None:
        engine = RemoteEngine(self._client)
        overlay = OverlayRenderer()
        scene = GameScene(
            self._canvas,
            BoardRenderer(self._asset(self._settings.board_asset)),
            PieceRenderer(self._asset(self._settings.pieces_asset)),
            overlay,
            engine,
            MoveHistoryRenderer(),
        )
        account = AccountStatusRenderer(self._settings)
        network = NetworkStatusRenderer(self._settings)
        result = GameResultPresenter(overlay)
        if self._client.role != "spectator":
            MouseHandler(engine.controller).register(self._title)
        while True:
            frame = scene.render()
            account.draw(frame, self._client)
            network.draw(frame, self._client)
            result.draw(frame, self._client)
            cv2.imshow(self._title, frame.img)
            key = cv2.waitKey(1000 // FPS) & 0xFF
            if (
                key == KeyBindings.ESCAPE
                or KeyBindings.is_key(key, "q")
            ):
                return

    @staticmethod
    def _asset(name):
        return os.path.join(ASSETS_DIR, name)
