"""Configurable settings for authenticated multiplayer."""

from dataclasses import dataclass
import json
import os


@dataclass(frozen=True)
class EloSettings:
    starting_rating: int
    k_factor: float
    rating_divisor: float
    base: float


@dataclass(frozen=True)
class PasswordSettings:
    algorithm: str
    iterations: int
    salt_bytes: int
    derived_key_bytes: int


@dataclass(frozen=True)
class MultiplayerSettings:
    database_path: str
    elo: EloSettings
    password: PasswordSettings
    session_token_bytes: int


def load_settings(config_path: str | None = None) -> MultiplayerSettings:
    path = config_path or os.path.join(os.path.dirname(__file__), "multiplayer_settings.json")
    with open(path, encoding="utf-8") as file:
        raw = json.load(file)
    elo = raw["elo"]
    password = raw["password"]
    database_path = os.environ.get("KUNG_FU_CHESS_DB_PATH", raw["database_path"])
    return MultiplayerSettings(
        database_path=database_path,
        elo=EloSettings(
            starting_rating=int(os.environ.get("KUNG_FU_CHESS_STARTING_RATING", elo["starting_rating"])),
            k_factor=float(os.environ.get("KUNG_FU_CHESS_ELO_K_FACTOR", elo["k_factor"])),
            rating_divisor=float(os.environ.get("KUNG_FU_CHESS_ELO_DIVISOR", elo["rating_divisor"])),
            base=float(os.environ.get("KUNG_FU_CHESS_ELO_BASE", elo["base"])),
        ),
        password=PasswordSettings(**password),
        session_token_bytes=int(raw["session"]["token_bytes"]),
    )
