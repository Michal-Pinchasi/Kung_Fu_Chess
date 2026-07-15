"""
Translates OpenCV mouse events into game engine clicks.

The window is displayed at 1:1 pixel ratio with the image,
so no coordinate scaling is needed.
"""

import cv2


class MouseHandler:
    """Listens for OpenCV left-click events and forwards them to the engine."""

    def __init__(self, engine):
        self._engine = engine

    def register(self, window_name: str) -> None:
        """Attach this handler to an already-visible OpenCV window."""
        cv2.setMouseCallback(window_name, self._on_mouse)

    def _on_mouse(self, event: int, px: int, py: int, flags: int, param) -> None:
        """Forward left-click pixel coordinates directly to the engine."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self._engine.click_at_window_pixel(px, py)
