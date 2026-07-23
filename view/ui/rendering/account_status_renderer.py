"""Authenticated account status rendering during a game."""


class AccountStatusRenderer:
    def __init__(self, settings):
        self._layout = settings.account_status
        self._colors = settings.colors
        self._alpha = settings.alpha["panel"]
        self._thickness = settings.text_thickness

    def draw(self, frame, client) -> None:
        color_name = self._color_name(client)
        frame.draw_rect(
            *self._layout["panel"],
            color=self._colors["panel"],
            alpha=self._alpha,
        )
        x, y, size = self._layout["identity"]
        frame.put_text(
            f"{client.username} | {color_name} | ELO {client.rating}",
            x,
            y,
            size,
            color=self._colors["white"],
            thickness=self._thickness,
        )
        if client.game_result:
            x, y, size = self._layout["result"]
            outcome = client.game_result["outcome"].upper()
            frame.put_text(
                f"RESULT: {outcome} | NEW ELO: {client.rating}",
                x,
                y,
                size,
                color=self._colors["accent"],
                thickness=self._thickness,
            )

    @staticmethod
    def _color_name(client) -> str:
        if client.role == "spectator":
            return "SPECTATOR"
        return "WHITE" if client.color == "w" else "BLACK"
