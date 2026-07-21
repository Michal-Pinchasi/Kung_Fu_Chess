"""Configurable settings for authenticated multiplayer."""

from dataclasses import dataclass, field
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
class MatchmakingSettings:
    elo_range: int = 100
    queue_timeout_seconds: float = 60.0
    poll_interval_seconds: float = 0.25


@dataclass(frozen=True)
class DisconnectSettings:
    grace_period_seconds: float = 25.0
    countdown_interval_seconds: float = 1.0


@dataclass(frozen=True)
class ReconnectSettings:
    initial_delay_seconds: float = 0.5
    maximum_delay_seconds: float = 4.0


@dataclass(frozen=True)
class RoomSettings:
    player_capacity: int = 2
    maximum_spectators: int = 20
    room_id_bytes: int = 6
    local_spectator_windows: int = 1


@dataclass(frozen=True)
class LoggingSettings:
    server_log_path: str = "logs/server.log"
    client_log_directory: str = "logs/clients"
    level: str = "INFO"
    maximum_file_bytes: int = 5_242_880
    backup_count: int = 5


@dataclass(frozen=True)
class MultiplayerSettings:
    database_path: str
    elo: EloSettings
    password: PasswordSettings
    session_token_bytes: int
    matchmaking: MatchmakingSettings = field(default_factory=MatchmakingSettings)
    disconnect: DisconnectSettings = field(default_factory=DisconnectSettings)
    reconnect: ReconnectSettings = field(default_factory=ReconnectSettings)
    rooms: RoomSettings = field(default_factory=RoomSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)


def load_settings(config_path: str | None = None) -> MultiplayerSettings:
    path = config_path or os.path.join(os.path.dirname(__file__), "multiplayer_settings.json")
    with open(path, encoding="utf-8") as file:
        raw = json.load(file)
    elo = raw["elo"]
    password = raw["password"]
    matchmaking = raw.get("matchmaking", {})
    disconnect = raw.get("disconnect", {})
    reconnect = raw.get("reconnect", {})
    rooms = raw.get("rooms", {})
    logging_settings = raw.get("logging", {})
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
        matchmaking=MatchmakingSettings(
            elo_range=int(os.environ.get("KUNG_FU_CHESS_ELO_RANGE", matchmaking.get("elo_range", 100))),
            queue_timeout_seconds=float(os.environ.get("KUNG_FU_CHESS_QUEUE_TIMEOUT", matchmaking.get("queue_timeout_seconds", 60))),
            poll_interval_seconds=float(matchmaking.get("poll_interval_seconds", 0.25)),
        ),
        disconnect=DisconnectSettings(
            grace_period_seconds=float(os.environ.get("KUNG_FU_CHESS_DISCONNECT_GRACE", disconnect.get("grace_period_seconds", 25))),
            countdown_interval_seconds=float(disconnect.get("countdown_interval_seconds", 1)),
        ),
        reconnect=ReconnectSettings(
            initial_delay_seconds=float(reconnect.get("initial_delay_seconds", 0.5)),
            maximum_delay_seconds=float(reconnect.get("maximum_delay_seconds", 4)),
        ),
        rooms=RoomSettings(
            player_capacity=int(os.environ.get("KUNG_FU_CHESS_ROOM_PLAYER_CAPACITY", rooms.get("player_capacity", 2))),
            maximum_spectators=int(os.environ.get("KUNG_FU_CHESS_MAX_SPECTATORS", rooms.get("maximum_spectators", 20))),
            room_id_bytes=int(rooms.get("room_id_bytes", 6)),
            local_spectator_windows=int(rooms.get("local_spectator_windows", 1)),
        ),
        logging=LoggingSettings(
            server_log_path=os.environ.get("KUNG_FU_CHESS_SERVER_LOG", logging_settings.get("server_log_path", "logs/server.log")),
            client_log_directory=os.environ.get("KUNG_FU_CHESS_CLIENT_LOG_DIR", logging_settings.get("client_log_directory", "logs/clients")),
            level=os.environ.get("KUNG_FU_CHESS_LOG_LEVEL", logging_settings.get("level", "INFO")),
            maximum_file_bytes=int(logging_settings.get("maximum_file_bytes", 5_242_880)),
            backup_count=int(logging_settings.get("backup_count", 5)),
        ),
    )
