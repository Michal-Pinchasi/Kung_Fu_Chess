"""Rendering for the authentication screen."""


class LoginScreenRenderer:
    """Draws authentication state without reading input or calling the client."""

    def __init__(self, settings):
        self._settings = settings
        self._layout = settings.login

    def draw(
        self,
        frame,
        username,
        password,
        username_active,
        register_mode,
        submitted,
        error,
    ) -> None:
        colors = self._settings.colors
        frame.draw_rect(
            *self._layout["panel"],
            color=colors["panel"],
            alpha=self._settings.alpha["login_panel"],
        )
        self._put(
            frame,
            "KUNG FU CHESS",
            "title",
            colors["accent"],
            self._settings.title_thickness,
        )
        self._put(
            frame,
            "Create account" if register_mode else "Sign in",
            "heading",
        )
        self._draw_field(
            frame, "Username", username, "username", username_active
        )
        self._draw_field(
            frame, "Password", "*" * len(password), "password", not username_active
        )
        frame.draw_rect(
            *self._layout["mode_button"],
            color=colors["accent"],
            thickness=self._settings.text_thickness,
        )
        target = "LOGIN" if register_mode else "REGISTER"
        self._put(frame, f"CLICK: switch to {target}", "mode_text")
        action = "REGISTER" if register_mode else "LOGIN"
        self._put(
            frame,
            f"ENTER: {action}   TAB: next field   ESC: exit",
            "help_text",
        )
        if submitted:
            status = error or "Connecting..."
            color = colors["error"] if error else colors["pending"]
            self._put(frame, status, "status", color)

    def _draw_field(self, frame, label, value, layout_key, active) -> None:
        x, y = self._layout[layout_key]
        frame.put_text(label, x, y, self._layout["field_label_size"])
        frame.draw_rect(
            x,
            y + self._layout["field_top_offset"],
            self._layout["field_width"],
            self._layout["field_height"],
            color=self._settings.colors["white"],
            thickness=self._settings.text_thickness if active else 1,
        )
        frame.put_text(
            value,
            x + self._layout["field_text_x_offset"],
            y + self._layout["field_text_y_offset"],
            self._layout["field_value_size"],
            color=self._settings.colors["white"],
            thickness=self._settings.text_thickness,
        )

    def _put(self, frame, text, layout_key, color=None, thickness=None) -> None:
        x, y, size = self._layout[layout_key]
        frame.put_text(
            text,
            x,
            y,
            size,
            color=color or self._settings.colors["white"],
            thickness=thickness or self._settings.text_thickness,
        )
