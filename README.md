# Kung Fu Chess

Real-time, turn-less multiplayer chess with an authoritative Python WebSocket server and OpenCV clients.

## Features (Phases 1-5)

- Real-time movement, jumping, captures, cooldowns, scoring, and king capture.
- SQLite users, statistics, and configurable ELO (default starting rating: 1200).
- PBKDF2 password hashing with a unique secure salt; plaintext passwords are never stored.
- OpenCV login and registration screen inside the game window.
- Rating-based Quick Play matchmaking (default range: +/-100 ELO).
- Configurable queue timeout (default: 60 seconds).
- Independent games identified by secure `game_id` values.
- Snapshot sequence numbers and stale-snapshot rejection.
- Automatic reconnect with a configurable 20-30 second grace period.
- Technical forfeit and one-time ELO update when reconnect expires.
- Secure private rooms identified by generated room IDs.
- Server-assigned roles: first member White, second Black, later members Spectators.
- Read-only spectators receive board updates, animations, countdowns, and results.
- Rotating server/client logs with automatic credential and token redaction.

## Install and run

Install dependencies once:

```powershell
python -m pip install -r requirements.txt
```

Start the server and local clients:

```powershell
python start_local_match.py
```

Alternatively, double-click `start_local_match.bat`.

The local launcher opens a configurable number of clients. The default is two player windows plus one spectator window.

## Login and registration

- Click the on-screen mode button to switch between Login and Register.
- `Tab`: switch between username and password.
- `Enter`: submit.
- `Esc`: exit.
- All letters, including `R` and `Q`, can be typed normally in credentials.

Passwords are stored only as salted PBKDF2 hashes in `data/kung_fu_chess.sqlite3`.

## Room menu

- `P`, `Enter`, `Space`, or the Quick Play button: join/cancel matchmaking.
- `C` or Create Room: create a private room and display its room ID.
- `J` or Join Room: enter an existing room ID, then press `Enter`.
- `L`: leave a room that is still waiting for players.
- `Esc`: exit.

Private-room role assignment is server-controlled:

1. First member: White.
2. Second member: Black.
3. Every later member: Spectator.

Spectators never receive input control and the server rejects manually forged commands with `spectator_read_only`.

## Game controls

- Left-click a friendly piece, then left-click a destination: move.
- Right-click a friendly piece: jump.
- `Q` or `Esc`: close the game window.

At game over, the overlay displays the winning username, color, and `WINS`, or `DRAW`.

## Matchmaking and resilience

Quick Play matches players inside the configured rating window. A player who is not matched before the queue timeout receives `matchmaking_timeout` and returns to the room menu.

If a player disconnects during a game:

1. The server preserves the authoritative game and room state.
2. The opponent and spectators receive a live countdown.
3. The client retries with its session token and game ID.
4. A successful reconnect restores the same role and latest snapshot.
5. If the window was closed and reopened, a normal Login automatically resumes the disconnected game while the grace period is active.
6. An expired grace period produces a technical forfeit, updates ELO once, and releases the finished room so Quick Play can start a new game.

Quick Play never resumes an old game; it is reserved for new matchmaking.

Snapshots include a monotonically increasing sequence number. Clients ignore snapshots older than the last accepted sequence.

## Configuration

Runtime values live in `config/multiplayer_settings.json`, including:

- SQLite path and password hashing parameters.
- Starting ELO, K-factor, rating divisor, and formula base.
- Matchmaking range and timeout.
- Disconnect grace period and reconnect backoff.
- Player/spectator capacities and local spectator windows.
- Log paths, levels, rotation size, and backup count.

Environment overrides include:

```text
KUNG_FU_CHESS_DB_PATH
KUNG_FU_CHESS_STARTING_RATING
KUNG_FU_CHESS_ELO_K_FACTOR
KUNG_FU_CHESS_ELO_DIVISOR
KUNG_FU_CHESS_ELO_BASE
KUNG_FU_CHESS_ELO_RANGE
KUNG_FU_CHESS_QUEUE_TIMEOUT
KUNG_FU_CHESS_DISCONNECT_GRACE
KUNG_FU_CHESS_ROOM_PLAYER_CAPACITY
KUNG_FU_CHESS_MAX_SPECTATORS
KUNG_FU_CHESS_SERVER_LOG
KUNG_FU_CHESS_CLIENT_LOG_DIR
KUNG_FU_CHESS_LOG_LEVEL
```

## Logging

- Server audit log: `logs/server.log` by default.
- Client logs: `logs/clients/` by default.
- Logs rotate according to the configured maximum size and backup count.
- Authentication, connection, room, role, command, game-event, reconnect, result, and error events are audited.
- Passwords, password hashes, salts, session tokens, and authorization values are replaced with `[REDACTED]`.

Runtime logs and launcher output are ignored by Git.

## Tests

Run the automated suite without the manual OpenCV visual test:

```powershell
python -m pytest -q --ignore=tests/test_visual.py
```

Current verified result:

```text
233 passed, 1 skipped
```

The skipped test is an intentionally manual OpenCV display check.
