"""Loads configurable layout and theme values for the network UI."""

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkUiSettings:
    default_server_uri: str
    background_asset: str
    board_asset: str
    pieces_asset: str
    login: dict
    account_status: dict
    network_status: dict
    colors: dict
    alpha: dict
    text_thickness: int
    title_thickness: int


def load_network_ui_settings(config_path=None) -> NetworkUiSettings:
    path = config_path or os.path.join(os.path.dirname(__file__), "network_ui.json")
    with open(path, encoding="utf-8") as file:
        raw = json.load(file)
    raw["colors"] = {
        name: tuple(value) for name, value in raw["colors"].items()
    }
    return NetworkUiSettings(**raw)
