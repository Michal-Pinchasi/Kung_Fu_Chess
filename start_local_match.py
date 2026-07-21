"""Start one local server and two independent graphical player windows."""

import os
import subprocess
import sys
import time


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    # The player sees the two OpenCV game windows, not three extra consoles.
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    server = subprocess.Popen([sys.executable, "-m", "network.websocket_server"], cwd=root,
                              creationflags=creationflags)
    try:
        # The server only binds localhost and normally starts in well under a second.
        time.sleep(0.8)
        if server.poll() is not None:
            raise RuntimeError("The local server did not start. Check its console for details.")
        subprocess.Popen([sys.executable, "-m", "view.ui.net_app", "--window-name", "Kung Fu Chess - Player 1"],
                         cwd=root, creationflags=creationflags)
        time.sleep(0.3)  # guarantees Player 1 receives white before Player 2 connects
        subprocess.Popen([sys.executable, "-m", "view.ui.net_app", "--window-name", "Kung Fu Chess - Player 2"],
                         cwd=root, creationflags=creationflags)
    except Exception:
        server.terminate()
        raise


if __name__ == "__main__":
    main()
