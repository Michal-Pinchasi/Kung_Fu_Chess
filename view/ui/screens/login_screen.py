"""Graphical authentication screen."""

import cv2

from network.client.connection_state import ConnectionState
from view.ui.config.ui_config_loader import FPS
from view.ui.input.key_bindings import KeyBindings
from view.ui.rendering.login_screen_renderer import LoginScreenRenderer


class LoginScreen:
    """Collects credentials and invokes the network authentication API."""

    USERNAME_FIELD = 0
    PASSWORD_FIELD = 1

    def __init__(self, client, canvas, title, settings):
        self._client = client
        self._canvas = canvas
        self._title = title
        self._settings = settings
        self._layout = settings.login
        self._renderer = LoginScreenRenderer(settings)
        self._mode_clicked = False

    def run(self) -> bool:
        username, password = "", ""
        active_field = self.USERNAME_FIELD
        register_mode, submitted = False, False
        cv2.setMouseCallback(self._title, self._on_mouse)
        while True:
            self._draw(username, password, active_field, register_mode, submitted)
            key = cv2.waitKeyEx(1000 // FPS)
            if key == KeyBindings.ESCAPE:
                return False
            if self._client.username is not None and self._client.state in (
                ConnectionState.LOBBY,
                ConnectionState.PLAYING,
                ConnectionState.SPECTATING,
            ):
                return True
            if key == KeyBindings.TAB:
                active_field = (
                    self.PASSWORD_FIELD
                    if active_field == self.USERNAME_FIELD
                    else self.USERNAME_FIELD
                )
            elif self._consume_mode_click():
                register_mode, submitted = not register_mode, False
                self._client.error = None
            elif key in KeyBindings.BACKSPACE:
                if active_field == self.USERNAME_FIELD:
                    username = username[:-1]
                else:
                    password = password[:-1]
            elif key in KeyBindings.ENTER and username and password:
                submitted = True
                self._client.authenticate(username, password, register_mode)
            elif KeyBindings.is_printable(key):
                if active_field == self.USERNAME_FIELD:
                    username += chr(key)
                else:
                    password += chr(key)

    def _draw(
        self, username, password, active_field, register_mode, submitted
    ) -> None:
        frame = self._canvas.fresh_frame()
        self._renderer.draw(
            frame,
            username,
            password,
            active_field == self.USERNAME_FIELD,
            register_mode,
            submitted,
            self._client.error,
        )
        cv2.imshow(self._title, frame.img)

    def _on_mouse(self, event, x, y, _flags, _param) -> None:
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        box_x, box_y, box_w, box_h = self._layout["mode_button"]
        self._mode_clicked = (
            box_x <= x <= box_x + box_w and box_y <= y <= box_y + box_h
        )

    def _consume_mode_click(self) -> bool:
        clicked, self._mode_clicked = self._mode_clicked, False
        return clicked
