"""Resilient threaded WebSocket client for the OpenCV application."""

import asyncio
import json
import queue
import threading

import websockets

from config.multiplayer_settings import load_settings
from network.client.connection_state import ConnectionState
from network.snapshot_deserializer import deserialize


class RemoteGameClient:
    def __init__(self, uri="ws://localhost:8765", settings=None):
        self.uri = uri
        self.settings = settings or load_settings()
        self.state = ConnectionState.CONNECTING
        self.color = self.username = self.rating = self.token = None
        self.game_id = self.opponent = self.game_result = self.error = None
        self.queue_timeout_seconds = None
        self.opponent_disconnect_seconds = None
        self.notification = None
        self._snapshot = None
        self._last_sequence = -1
        self._lock = threading.Lock()
        self._authenticated = threading.Event()
        self._stop = threading.Event()
        self._outgoing = queue.Queue()
        self._loop = self._websocket = self._thread = None

    def connect(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, daemon=True, name="kung-fu-ws-client")
            self._thread.start()

    def authenticate(self, username, password, register=False):
        self.error = None
        self.state = ConnectionState.AUTHENTICATING
        self._authenticated.clear()
        self._queue({"type": "auth", "mode": "register" if register else "login",
                     "username": username, "password": password})

    def join_queue(self):
        if self.state != ConnectionState.LOBBY:
            return False
        self._queue({"type": "join_queue"})
        return True

    def leave_queue(self):
        if self.state != ConnectionState.SEARCHING:
            return False
        self._queue({"type": "leave_queue"})
        return True

    def latest_snapshot(self):
        with self._lock:
            return self._snapshot

    def send_command(self, command):
        if self.state != ConnectionState.PLAYING or self._stop.is_set():
            return False
        self._outgoing.put(command)
        return True

    def close(self):
        self._stop.set()
        self.state = ConnectionState.CLOSED
        if self._loop and self._websocket:
            asyncio.run_coroutine_threadsafe(self._websocket.close(), self._loop)
        if self._thread:
            self._thread.join(timeout=2)

    def _queue(self, payload):
        self._outgoing.put(json.dumps(payload))

    def _run(self):
        asyncio.run(self._connection_loop())

    async def _connection_loop(self):
        delay = self.settings.reconnect.initial_delay_seconds
        while not self._stop.is_set():
            try:
                await self._run_once()
                if not self.game_id or self.state == ConnectionState.GAME_OVER:
                    break
            except (OSError, websockets.ConnectionClosed):
                if not self.game_id:
                    self.error = "Connection to server was lost."
                    break
            if self._stop.is_set():
                break
            self.state = ConnectionState.RECONNECTING
            self.notification = "Connection lost - reconnecting..."
            await asyncio.sleep(delay)
            delay = min(delay * 2, self.settings.reconnect.maximum_delay_seconds)

    async def _run_once(self):
        self._loop = asyncio.get_running_loop()
        async with websockets.connect(self.uri) as websocket:
            self._websocket = websocket
            if self.state == ConnectionState.RECONNECTING and self.token and self.game_id:
                await websocket.send(json.dumps({"type": "reconnect", "token": self.token,
                                                 "game_id": self.game_id}))
            receiver = asyncio.create_task(self._receive(websocket))
            sender = asyncio.create_task(self._send(websocket))
            done, pending = await asyncio.wait((receiver, sender), return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                error = task.exception()
                if error:
                    raise error

    async def _receive(self, websocket):
        async for raw in websocket:
            self._handle_event(json.loads(raw))

    def _handle_event(self, message):
        kind = message["type"]
        if kind == "auth_result":
            self.username, self.rating, self.token = message["username"], message["rating"], message["token"]
            self._authenticated.set()
        elif kind == "lobby_ready":
            self.state = ConnectionState.LOBBY
        elif kind == "queue_joined":
            self.state = ConnectionState.SEARCHING
            self.queue_timeout_seconds = message["timeout_seconds"]
            self.notification = "Searching for an opponent..."
        elif kind in ("queue_left", "matchmaking_timeout"):
            self.state = ConnectionState.LOBBY
            self.notification = "Search timed out." if kind == "matchmaking_timeout" else "Search cancelled."
        elif kind == "match_found":
            self.game_id, self.color, self.opponent = message["game_id"], message["color"], message["opponent"]
            self.state, self.notification = ConnectionState.PLAYING, "Match found!"
            self._last_sequence = -1
        elif kind == "snapshot" and message.get("game_id") == self.game_id:
            if message["sequence"] > self._last_sequence:
                with self._lock:
                    self._snapshot = deserialize(message["data"])
                    self._last_sequence = message["sequence"]
        elif kind == "opponent_disconnected":
            self.opponent_disconnect_seconds = message["remaining_seconds"]
        elif kind == "opponent_reconnected":
            self.opponent_disconnect_seconds = None
            self.notification = "Opponent reconnected."
        elif kind == "reconnect_success":
            self.username, self.rating = message["username"], message["rating"]
            self.color, self.game_id = message["color"], message["game_id"]
            self.state, self.notification = ConnectionState.PLAYING, "Reconnected."
        elif kind == "game_result":
            self.game_result, self.rating = message, message["rating"]
            self.state = ConnectionState.GAME_OVER
        elif kind in ("error", "auth_error", "matchmaking_error"):
            self.error = message["reason"]
            if kind == "auth_error":
                self._authenticated.set()

    async def _send(self, websocket):
        while not self._stop.is_set():
            try:
                command = await asyncio.to_thread(self._outgoing.get, True, 0.2)
            except queue.Empty:
                continue
            await websocket.send(command)
