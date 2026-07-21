"""Real WebSocket integration coverage for authentication, matchmaking and recovery."""

import asyncio
import json
import tempfile
from dataclasses import replace

import websockets

from config.multiplayer_settings import load_settings, MatchmakingSettings
from network.websocket_server import GameServer


async def _start_server(timeout=60):
    tempdir = tempfile.TemporaryDirectory()
    base = load_settings()
    settings = replace(base, database_path=f"{tempdir.name}/test.sqlite3",
                       matchmaking=MatchmakingSettings(100, timeout, 0.01))
    server = GameServer(host="localhost", port=0, tick_ms=20, settings=settings)
    server._tempdir = tempdir
    server._start_task = asyncio.create_task(server.start())
    for _ in range(100):
        if server.bound_port is not None:
            return server
        await asyncio.sleep(0.01)
    raise TimeoutError("server did not bind")


async def _stop_server(server):
    server._start_task.cancel()
    try:
        await server._start_task
    except asyncio.CancelledError:
        pass
    server._tempdir.cleanup()


async def _recv_type(connection, kind):
    while True:
        message = json.loads(await asyncio.wait_for(connection.recv(), 2))
        if message["type"] == kind:
            return message


async def _register(connection, username):
    await connection.send(json.dumps({"type": "auth", "mode": "register",
                                      "username": username, "password": "password"}))
    auth = await _recv_type(connection, "auth_result")
    await _recv_type(connection, "lobby_ready")
    return auth


async def _match(first, second):
    await first.send(json.dumps({"type": "join_queue"}))
    await _recv_type(first, "queue_joined")
    await second.send(json.dumps({"type": "join_queue"}))
    await _recv_type(second, "queue_joined")
    return await _recv_type(first, "match_found"), await _recv_type(second, "match_found")


def test_players_match_and_receive_isolated_game_snapshot():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as first, websockets.connect(uri) as second:
                await _register(first, "white")
                await _register(second, "black")
                first_match, second_match = await _match(first, second)
                assert first_match["game_id"] == second_match["game_id"]
                assert {first_match["color"], second_match["color"]} == {"w", "b"}
                snapshot = await _recv_type(first, "snapshot")
                assert snapshot["game_id"] == first_match["game_id"]
                assert snapshot["sequence"] > 0
        finally:
            await _stop_server(server)
    asyncio.run(scenario())


def test_leave_queue_and_timeout_events():
    async def scenario():
        server = await _start_server(timeout=0.05)
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as player:
                await _register(player, "waiting")
                await player.send(json.dumps({"type": "join_queue"}))
                await _recv_type(player, "queue_joined")
                assert (await _recv_type(player, "matchmaking_timeout"))["type"] == "matchmaking_timeout"
                await player.send(json.dumps({"type": "join_queue"}))
                await _recv_type(player, "queue_joined")
                await player.send(json.dumps({"type": "leave_queue"}))
                assert (await _recv_type(player, "queue_left"))["was_queued"]
        finally:
            await _stop_server(server)
    asyncio.run(scenario())


def test_disconnect_reconnect_restores_latest_snapshot():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            first = await websockets.connect(uri)
            second = await websockets.connect(uri)
            first_auth = await _register(first, "returning")
            await _register(second, "opponent")
            first_match, _ = await _match(first, second)
            await _recv_type(first, "snapshot")
            await first.close()
            notice = await _recv_type(second, "opponent_disconnected")
            assert notice["remaining_seconds"] > 0

            async with websockets.connect(uri) as reconnected:
                await reconnected.send(json.dumps({"type": "reconnect", "token": first_auth["token"],
                                                   "game_id": first_match["game_id"]}))
                assert (await _recv_type(reconnected, "reconnect_success"))["color"] == first_match["color"]
                snapshot = await _recv_type(reconnected, "snapshot")
                assert snapshot["game_id"] == first_match["game_id"]
                assert (await _recv_type(second, "opponent_reconnected"))["type"] == "opponent_reconnected"
            await second.close()
        finally:
            await _stop_server(server)
    asyncio.run(scenario())


def test_game_commands_require_active_match_and_correct_color():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as first, websockets.connect(uri) as second:
                await _register(first, "one")
                await first.send("WPe2e4")
                assert (await _recv_type(first, "error"))["reason"] == "not_in_active_game"
                await _register(second, "two")
                first_match, second_match = await _match(first, second)
                white = first if first_match["color"] == "w" else second
                await white.send("BPe7e5")
                assert (await _recv_type(white, "error"))["reason"] == "not_your_piece"
        finally:
            await _stop_server(server)
    asyncio.run(scenario())


def test_disconnect_expiry_causes_single_rated_technical_forfeit():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            loser = await websockets.connect(uri)
            winner = await websockets.connect(uri)
            await _register(loser, "forfeit-loser")
            await _register(winner, "forfeit-winner")
            loser_match, _ = await _match(loser, winner)
            await loser.close()
            await _recv_type(winner, "opponent_disconnected")
            state = next(iter(server.disconnects._states.values()))
            state.deadline = 0
            result = await _recv_type(winner, "game_result")
            assert result["reason"] == "technical_forfeit"
            assert result["outcome"] == "win"
            assert server.repository.get_by_username("forfeit-winner").wins == 1
            assert server.repository.get_by_username("forfeit-loser").losses == 1
            final_snapshot = await _recv_type(winner, "snapshot")
            assert final_snapshot["game_id"] == loser_match["game_id"]
            await asyncio.sleep(0.05)
            assert server.repository.get_by_username("forfeit-winner").wins == 1
            await winner.close()
        finally:
            await _stop_server(server)
    asyncio.run(scenario())


def test_private_room_assigns_players_and_read_only_spectator():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as first, websockets.connect(uri) as second, websockets.connect(uri) as viewer:
                await _register(first, "room-white")
                await _register(second, "room-black")
                await _register(viewer, "room-viewer")

                await first.send(json.dumps({"type": "create_room"}))
                created = await _recv_type(first, "room_created")
                assert created["role"] == "white"

                await second.send(json.dumps({"type": "join_room", "room_id": created["room_id"]}))
                assert (await _recv_type(second, "room_joined"))["role"] == "black"
                first_match = await _recv_type(first, "match_found")
                await _recv_type(second, "match_found")

                await viewer.send(json.dumps({"type": "join_room", "room_id": created["room_id"]}))
                assert (await _recv_type(viewer, "room_joined"))["role"] == "spectator"
                viewer_match = await _recv_type(viewer, "match_found")
                assert viewer_match["game_id"] == first_match["game_id"]
                assert viewer_match["color"] is None
                await _recv_type(viewer, "snapshot")

                await viewer.send("WPe2e4")
                assert (await _recv_type(viewer, "error"))["reason"] == "spectator_read_only"
        finally:
            await _stop_server(server)
    asyncio.run(scenario())
