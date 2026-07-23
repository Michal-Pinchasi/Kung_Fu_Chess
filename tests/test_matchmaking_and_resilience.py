from types import SimpleNamespace

import pytest

from matchmaking.matchmaking_manager import MatchmakingManager
from network.disconnect_manager import DisconnectManager
from network.client.connection_state import ConnectionState
from network.client.remote_game_client import RemoteGameClient
from config.multiplayer_settings import load_settings


def user(user_id, rating):
    return SimpleNamespace(id=user_id, username=f"u{user_id}", rating=rating)


def test_matchmaking_pairs_only_inside_configured_elo_window():
    now = [0.0]
    manager = MatchmakingManager(100, 60, clock=lambda: now[0])
    manager.join(user(1, 1200), "a")
    manager.join(user(2, 1301), "b")
    assert manager.find_matches() == []
    manager.join(user(3, 1299), "c")
    matches = manager.find_matches()
    assert len(matches) == 1
    assert {matches[0][0].user.id, matches[0][1].user.id} == {1, 3}


def test_matchmaking_prefers_closest_rating_then_wait_time():
    times = iter((0.0, 1.0, 2.0))
    manager = MatchmakingManager(100, 60, clock=lambda: next(times))
    manager.join(user(1, 1200), "a")
    manager.join(user(2, 1250), "b")
    manager.join(user(3, 1205), "c")
    first = manager.find_matches()[0]
    assert {first[0].user.id, first[1].user.id} == {1, 3}


def test_queue_timeout_removes_player():
    now = [0.0]
    manager = MatchmakingManager(100, 60, clock=lambda: now[0])
    manager.join(user(1, 1200), "socket")
    now[0] = 60.0
    assert [entry.user.id for entry in manager.expired()] == [1]
    assert len(manager) == 0


def test_duplicate_queue_entry_is_rejected():
    manager = MatchmakingManager(100, 60, clock=lambda: 0)
    manager.join(user(1, 1200), "a")
    with pytest.raises(ValueError, match="already_in_queue"):
        manager.join(user(1, 1200), "b")


def test_disconnect_countdown_can_be_cancelled_on_reconnect():
    now = [10.0]
    manager = DisconnectManager(25, clock=lambda: now[0])
    manager.start("game", 7)
    assert manager.updates()[0][1] == 25
    now[0] = 11.2
    assert manager.updates()[0][1] == 24
    assert manager.cancel("game", 7)
    now[0] = 40
    assert manager.expired() == []


def test_disconnect_states_can_be_cleared_for_finished_game():
    manager = DisconnectManager(25, clock=lambda: 0)
    manager.start("finished", 1)
    manager.start("finished", 2)
    manager.start("active", 3)

    manager.cancel_game("finished")

    assert not manager.contains("finished", 1)
    assert not manager.contains("finished", 2)
    assert manager.contains("active", 3)


def test_disconnect_expiration_and_grace_validation():
    now = [0.0]
    manager = DisconnectManager(20, clock=lambda: now[0])
    manager.start("game", 1)
    now[0] = 20
    assert manager.expired()[0].user_id == 1
    with pytest.raises(ValueError):
        DisconnectManager(19)


def test_disconnect_cannot_be_cancelled_after_deadline():
    now = [0.0]
    manager = DisconnectManager(20, clock=lambda: now[0])
    manager.start("game", 1)
    now[0] = 20

    assert not manager.cancel("game", 1)
    assert not manager.contains("game", 1)


def test_client_ignores_out_of_order_snapshots():
    client = RemoteGameClient(settings=load_settings())
    client.game_id = "g"
    client.state = ConnectionState.PLAYING
    empty = {"board_width": 8, "board_height": 8, "pieces": [], "selected_cell": None,
             "game_over": False, "move_history": None, "score": None}
    client._handle_event({"type": "snapshot", "game_id": "g", "sequence": 5, "data": empty})
    first = client.latest_snapshot()
    stale = dict(empty, board_width=99)
    client._handle_event({"type": "snapshot", "game_id": "g", "sequence": 4, "data": stale})
    assert client.latest_snapshot() is first
    assert client.latest_snapshot().board_width == 8
