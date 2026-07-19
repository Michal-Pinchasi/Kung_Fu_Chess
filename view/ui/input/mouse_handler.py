"""
Translates OpenCV mouse events into controller commands.

The window is displayed at 1:1 pixel ratio with the image,
so no coordinate scaling is needed.
"""

import cv2


class MouseHandler:
    """Listens for OpenCV mouse events and forwards them to the controller.

    Left click: select/move a piece. Right click: request a defensive jump.
    """

    def __init__(self, controller):
        self._controller = controller

    def register(self, window_name: str) -> None:
        """Attach this handler to an already-visible OpenCV window."""
        cv2.setMouseCallback(window_name, self._on_mouse)

    def _on_mouse(self, event: int, px: int, py: int, flags: int, param) -> None:
        """Forward click pixel coordinates directly to the controller."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.handle_pixel_click(px, py)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._controller.handle_pixel_jump(px, py)
