"""Start one local server and two independent graphical player windows."""

import os
import subprocess
import sys
import time

from config.multiplayer_settings import load_settings


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    settings = load_settings()
    # The player sees the two OpenCV game windows, not three extra consoles.
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    server = subprocess.Popen([sys.executable, "-m", "network.websocket_server"], cwd=root,
                              creationflags=creationflags)
    try:
        # The server only binds localhost and normally starts in well under a second.
        time.sleep(0.8)
        if server.poll() is not None:
            raise RuntimeError("The local server did not start. Check its console for details.")
        client_count = settings.rooms.player_capacity + settings.rooms.local_spectator_windows
        for number in range(1, client_count + 1):
            subprocess.Popen([sys.executable, "-m", "view.ui.net_app", "--window-name",
                              f"Kung Fu Chess - Client {number}"], cwd=root, creationflags=creationflags)
            time.sleep(0.3)
    except Exception:
        server.terminate()
        raise


if __name__ == "__main__":
    main()
