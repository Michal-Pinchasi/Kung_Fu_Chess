"""
Async integration tests for GameServer.

Uses asyncio.run() directly inside plain (synchronous) pytest test
functions, so no pytest-asyncio plugin is required — consistent with
keeping new test-only dependencies to a minimum.

Each test starts a real GameServer on an OS-assigned free port
(port=0), connects real websockets clients to it over localhost, and
tears the server down in a finally block so no background task or open
socket leaks between tests.
"""

import asyncio
import json

import pytest
import websockets

from network.websocket_server import GameServer


async def _start_server(tick_ms: int = 50) -> GameServer:
    """Start a GameServer on an ephemeral local port and return it once bound."""
    server = GameServer(host="localhost", port=0, tick_ms=tick_ms)
    server._start_task = asyncio.create_task(server.start())

    for _ in range(100):
        if server.bound_port is not None:
            return server
        await asyncio.sleep(0.01)
    raise TimeoutError("GameServer did not bind to a port in time")


async def _stop_server(server: GameServer) -> None:
    """Cancel a server started by _start_server and wait for shutdown to finish."""
    server._start_task.cancel()
    try:
        await server._start_task
    except asyncio.CancelledError:
        pass


async def _recv_json(connection) -> dict:
    """Receive one WebSocket message and parse it as JSON."""
    return json.loads(await connection.recv())


async def _recv_type(connection, message_type: str) -> dict:
    """Receive messages until the requested type arrives.

    Snapshots are periodic and may legitimately arrive between a command being
    sent and its acknowledgement/error, so integration tests must not assume
    they are absent from that interval.
    """
    while True:
        message = await asyncio.wait_for(_recv_json(connection), timeout=1.0)
        if message["type"] == message_type:
            return message


def test_first_and_second_client_assigned_white_and_black():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as client_a:
                first_message = await _recv_json(client_a)
                assert first_message == {"type": "assigned_color", "color": "w"}

                async with websockets.connect(uri) as client_b:
                    second_message = await _recv_json(client_b)
                    assert second_message == {"type": "assigned_color", "color": "b"}
        finally:
            await _stop_server(server)

    asyncio.run(scenario())


def test_third_client_rejected_when_game_full():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as client_a, websockets.connect(uri) as client_b:
                await _recv_json(client_a)
                await _recv_json(client_b)

                async with websockets.connect(uri) as client_c:
                    message = await _recv_json(client_c)
                    assert message == {"type": "error", "reason": "game_full"}
        finally:
            await _stop_server(server)

    asyncio.run(scenario())


def test_legal_move_from_white_is_scheduled_and_broadcast():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as client_a:
                await _recv_json(client_a)  # assigned_color

                await client_a.send("WPe2e4")  # white pawn, legal double-step

                # Poll incoming broadcasts until the moved pawn shows as "moving".
                pawn_id = server.engine.board.get_piece(1, 4).id
                moving_seen = False
                for _ in range(50):
                    message = await asyncio.wait_for(_recv_json(client_a), timeout=1.0)
                    if message["type"] != "snapshot":
                        continue
                    pieces = {p["id"]: p for p in message["data"]["pieces"]}
                    if pawn_id in pieces and pieces[pawn_id]["state"] == "moving":
                        moving_seen = True
                        break

                assert moving_seen, "expected the moved pawn to appear as 'moving' in a broadcast"
        finally:
            await _stop_server(server)

    asyncio.run(scenario())


def test_command_for_opponent_piece_is_rejected():
    """A White connection sending a command targeting a Black piece is rejected,
    even though the wire command's own color letter is irrelevant to authorization."""
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as client_a:
                await _recv_json(client_a)  # assigned White

                await client_a.send("BPe7e5")  # targets a real Black pawn's square

                message = await _recv_type(client_a, "error")
                assert message == {"type": "error", "reason": "not_your_piece"}
        finally:
            await _stop_server(server)

    asyncio.run(scenario())


def test_malformed_command_returns_parse_error():
    async def scenario():
        server = await _start_server()
        try:
            uri = f"ws://localhost:{server.bound_port}"
            async with websockets.connect(uri) as client_a:
                await _recv_json(client_a)  # assigned_color

                await client_a.send("not a real command")

                message = await _recv_type(client_a, "error")
                assert message["type"] == "error"
        finally:
            await _stop_server(server)

    asyncio.run(scenario())
