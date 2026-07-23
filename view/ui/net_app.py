"""Command-line entry point for the graphical network client."""

import argparse
import os
import sys

# Legacy UI modules still use imports relative to this directory.
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

from view.ui.config.network_ui_loader import load_network_ui_settings
from view.ui.network_game_app import NetworkGameApp


def app(uri=None, window_name=None) -> None:
    settings = load_network_ui_settings()
    NetworkGameApp(
        uri or settings.default_server_uri, window_name, settings
    ).run()


if __name__ == "__main__":
    ui_settings = load_network_ui_settings()
    parser = argparse.ArgumentParser(description="Kung Fu Chess network client")
    parser.add_argument("--uri", default=ui_settings.default_server_uri)
    parser.add_argument("--window-name")
    arguments = parser.parse_args()
    app(arguments.uri, arguments.window_name)
