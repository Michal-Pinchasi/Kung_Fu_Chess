"""Room and automatic matchmaking screen."""

import cv2

from network.client.connection_state import ConnectionState
from view.ui.config.ui_config_loader import FPS
from view.ui.input.key_bindings import KeyBindings


class LobbyScreen:
    """Translates lobby keyboard/mouse input into client API calls."""

    def __init__(self, client, canvas, title, renderer):
        self._client = client
        self._canvas = canvas
        self._title = title
        self._renderer = renderer
        self._clicked_action = None

    def run(self) -> bool:
        join_mode, room_code = False, ""
        cv2.setMouseCallback(self._title, self._on_mouse)
        while True:
            self._draw(join_mode, room_code)
            key = cv2.waitKeyEx(1000 // FPS)
            if self._client.state in (
                ConnectionState.PLAYING,
                ConnectionState.SPECTATING,
            ):
                return True
            if key == KeyBindings.ESCAPE or KeyBindings.is_key(key, "q"):
                return False
            action = self._consume_action()
            if join_mode:
                join_mode, room_code = self._handle_room_code(
                    key, room_code
                )
            elif action == "join" or KeyBindings.is_key(key, "j"):
                join_mode, room_code = True, ""
            elif action == "create" or KeyBindings.is_key(key, "c"):
                self._client.create_room()
            elif KeyBindings.is_key(key, "l") and self._in_room:
                self._client.leave_room()
            elif self._is_quick_play(action, key):
                (
                    self._client.leave_queue()
                    if self._searching
                    else self._client.join_queue()
                )

    @property
    def _searching(self):
        return self._client.state == ConnectionState.SEARCHING

    @property
    def _in_room(self):
        return self._client.state == ConnectionState.IN_ROOM

    def _draw(self, join_mode, room_code) -> None:
        frame = self._canvas.fresh_frame()
        status = self._client.notification or "Choose how to play"
        if self._in_room:
            status = (
                f"ROOM: {self._client.room_id} | "
                f"{self._client.role.upper()} | Waiting for player..."
            )
        elif join_mode:
            status = f"ROOM ID: {room_code}_"
        self._renderer.draw(
            frame, self._client.username, self._client.rating, status
        )
        cv2.imshow(self._title, frame.img)

    def _handle_room_code(self, key, room_code):
        if key in KeyBindings.BACKSPACE:
            return True, room_code[:-1]
        if key in KeyBindings.ENTER and room_code:
            self._client.join_room(room_code)
            return False, room_code
        if KeyBindings.is_printable(key) and chr(key).isalnum():
            room_code += chr(key).upper()
        return True, room_code

    def _is_quick_play(self, action, key) -> bool:
        return (
            action == "quick"
            or key in KeyBindings.ENTER
            or key == KeyBindings.SPACE
            or KeyBindings.is_key(key, "p")
        )

    def _on_mouse(self, event, x, y, _flags, _param) -> None:
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        for action, box in self._renderer.action_boxes.items():
            box_x, box_y, box_w, box_h = box
            if box_x <= x <= box_x + box_w and box_y <= y <= box_y + box_h:
                self._clicked_action = action

    def _consume_action(self):
        action, self._clicked_action = self._clicked_action, None
        return action
