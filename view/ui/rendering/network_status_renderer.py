"""Connection loss and opponent disconnect rendering."""

from network.client.connection_state import ConnectionState


class NetworkStatusRenderer:
    def __init__(self, settings):
        self._layout = settings.network_status
        self._colors = settings.colors
        self._alpha = settings.alpha["network_panel"]
        self._thickness = settings.text_thickness

    def draw(self, frame, client) -> None:
        if client.state == ConnectionState.RECONNECTING:
            self._draw_reconnecting(frame)
        if client.opponent_disconnect_seconds is not None:
            self._draw_disconnect_countdown(
                frame, client.opponent_disconnect_seconds
            )

    def _draw_reconnecting(self, frame) -> None:
        frame.draw_rect(
            *self._layout["reconnecting_panel"],
            color=self._colors["dark_panel"],
            alpha=self._alpha,
        )
        self._put(
            frame,
            "CONNECTION LOST - RECONNECTING...",
            "reconnecting_text",
        )

    def _draw_disconnect_countdown(self, frame, seconds) -> None:
        frame.draw_rect(
            *self._layout["disconnect_panel"],
            color=self._colors["dark_panel"],
            alpha=self._alpha,
        )
        self._put(frame, "OPPONENT DISCONNECTED", "disconnect_title")
        self._put(
            frame,
            f"Technical win in {seconds}s",
            "disconnect_countdown",
            self._colors["white"],
        )

    def _put(self, frame, text, layout_key, color=None) -> None:
        x, y, size = self._layout[layout_key]
        frame.put_text(
            text,
            x,
            y,
            size,
            color=color or self._colors["warning"],
            thickness=self._thickness,
        )
