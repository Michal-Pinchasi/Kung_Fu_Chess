"""Threaded WebSocket client that keeps the OpenCV UI non-blocking."""

import asyncio
import json
import queue
import threading

import websockets

from network.snapshot_deserializer import deserialize


class RemoteGameClient:
    """Connect to one GameServer and expose its latest snapshot safely.

    WebSocket I/O runs on its own thread.  The OpenCV render loop can therefore
    keep drawing and handling mouse clicks normally on the main thread.
    """

    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.color = None
        self.error = None
        self._snapshot = None
        self._lock = threading.Lock()
        self._connected = threading.Event()
        self._closed = threading.Event()
        self._stop = threading.Event()
        self._outgoing = queue.Queue()
        self._loop = None
        self._websocket = None
        self._thread = None

    def connect(self) -> None:
        """Start connecting in the background (safe to call once)."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="kung-fu-ws-client")
        self._thread.start()

    def wait_until_ready(self, timeout: float = 5.0) -> bool:
        """Wait until the server assigned a color or reported an error."""
        self._connected.wait(timeout)
        return self.color is not None and self.error is None

    def latest_snapshot(self):
        with self._lock:
            return self._snapshot

    def send_command(self, command: str) -> bool:
        """Queue a wire command.  Returns False before the connection is ready."""
        if self.color is None or self._stop.is_set():
            return False
        self._outgoing.put(command)
        return True

    def close(self) -> None:
        """Close the socket and wait briefly for its I/O thread to finish."""
        self._stop.set()
        if self._loop is not None and self._websocket is not None:
            asyncio.run_coroutine_threadsafe(self._websocket.close(), self._loop)
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        try:
            asyncio.run(self._run_async())
        except OSError as error:
            self.error = f"Cannot connect to server: {error}"
            self._connected.set()
        finally:
            self._closed.set()

    async def _run_async(self) -> None:
        self._loop = asyncio.get_running_loop()
        try:
            async with websockets.connect(self.uri) as websocket:
                self._websocket = websocket
                receiver = asyncio.create_task(self._receive(websocket))
                sender = asyncio.create_task(self._send(websocket))
                done, pending = await asyncio.wait((receiver, sender), return_when=asyncio.FIRST_COMPLETED)
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                for task in done:
                    error = task.exception()
                    if error is not None:
                        raise error
        except websockets.ConnectionClosed:
            if not self._stop.is_set():
                self.error = "Connection to server was closed."
                self._connected.set()
        finally:
            self._websocket = None

    async def _receive(self, websocket) -> None:
        async for raw_message in websocket:
            message = json.loads(raw_message)
            if message["type"] == "assigned_color":
                self.color = message["color"]
                self._connected.set()
            elif message["type"] == "snapshot":
                with self._lock:
                    self._snapshot = deserialize(message["data"])
            elif message["type"] == "error":
                self.error = message["reason"]
                self._connected.set()

    async def _send(self, websocket) -> None:
        while not self._stop.is_set():
            try:
                command = await asyncio.to_thread(self._outgoing.get, True, 0.2)
            except queue.Empty:
                continue
            await websocket.send(command)
