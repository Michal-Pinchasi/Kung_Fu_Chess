import logging
from types import SimpleNamespace

import pytest

from config.multiplayer_settings import LoggingSettings, RoomSettings
from observability.logging_service import LoggingService, SensitiveDataFilter
from rooms.game_room import GameRoom
from rooms.room_manager import RoomManager
from rooms.room_role import RoomRole


def user(user_id, username=None):
    return SimpleNamespace(id=user_id, username=username or f"user{user_id}", rating=1200)


def test_room_assigns_first_two_players_then_spectators():
    room = GameRoom("ROOM", player_capacity=2, maximum_spectators=2, clock=lambda: 1.0)
    assert room.join(user(1), "a").role == RoomRole.WHITE
    assert room.join(user(2), "b").role == RoomRole.BLACK
    assert room.join(user(3), "c").role == RoomRole.SPECTATOR
    assert room.ready()
    assert room.spectator_count() == 1


def test_room_rejects_spectators_above_configured_capacity():
    room = GameRoom("ROOM", 2, 1)
    room.join(user(1), "a")
    room.join(user(2), "b")
    room.join(user(3), "c")
    with pytest.raises(ValueError, match="room_full"):
        room.join(user(4), "d")


def test_room_manager_creates_secure_ids_and_indexed_membership():
    manager = RoomManager(RoomSettings(player_capacity=2, maximum_spectators=3, room_id_bytes=6))
    room, owner = manager.create(user(1), "socket")
    assert room.room_id
    assert owner.role == RoomRole.WHITE
    assert manager.get(room.room_id.lower()) is room
    assert manager.for_user(1) is room


def test_reconnect_preserves_room_role():
    room = GameRoom("ROOM", 2, 3)
    member = room.join(user(1), "old")
    room.disconnect(1)
    restored = room.reconnect(1, "new")
    assert restored is member
    assert restored.role == RoomRole.WHITE
    assert restored.websocket == "new"


def test_sensitive_data_redaction_is_recursive():
    redacted = SensitiveDataFilter.redact({
        "username": "michal", "password": "secret", "nested": {"token": "abc", "value": 7},
    })
    assert redacted == {"username": "michal", "password": "[REDACTED]",
                        "nested": {"token": "[REDACTED]", "value": 7}}


def test_logging_service_writes_event_without_credentials(tmp_path):
    path = tmp_path / "audit.log"
    settings = LoggingSettings(server_log_path=str(path), level="INFO",
                               maximum_file_bytes=10_000, backup_count=1)
    service = LoggingService(settings)
    logger = service.create_logger(f"test.audit.{id(path)}", str(path))
    service.event(logger, logging.INFO, "login", username="michal", password="secret", token="abc")
    for handler in logger.handlers:
        handler.flush()
    content = path.read_text(encoding="utf-8")
    assert "michal" in content
    assert "secret" not in content
    assert "abc" not in content
    assert content.count("[REDACTED]") == 2
