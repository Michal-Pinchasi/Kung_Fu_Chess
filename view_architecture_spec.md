# View Architecture Specification - Kung Fu Chess (Phases 1-5)

## Principle

The OpenCV layer renders client state and translates input into client actions. It does not evaluate chess legality, assign room roles, calculate ELO, access SQLite, or mutate the authoritative board.

## Composition

```text
view/ui/net_app.py
`-- NetworkGameApp (screen transitions and resource lifetime)
    |-- LoginScreen + LoginScreenRenderer
    |-- LobbyScreen + RoomScreenRenderer
    |-- RemoteGameClient (threaded network state machine)
    |-- RemoteEngine (GameEngine-shaped network adapter)
    |-- Controller + MouseHandler (player input only)
    `-- GameScene
        |-- GameCanvas
        |-- BoardRenderer
        |-- PieceRenderer
        |-- MoveHistoryRenderer
        `-- OverlayRenderer
```

`network_ui.json` owns network-screen coordinates, colors, opacity, asset names, and the default server URI. `KeyBindings` gives OpenCV key codes semantic names.

## Client states

`ConnectionState` defines:

```text
CONNECTING
AUTHENTICATING
LOBBY
IN_ROOM
SEARCHING
PLAYING
SPECTATING
RECONNECTING
GAME_OVER
CLOSED
```

UI transitions are driven by server events received by `RemoteGameClient`.

## Screen flow

```text
Login/Register
  -> Room Menu
      |-- Quick Play -> Searching
      |-- Create Room -> In Room / waiting
      `-- Join Room -> Playing or Spectating
  -> Game Scene
  -> Game Over overlay
```

## Login screen

- Click the on-screen mode button to switch Login/Register.
- `Tab` changes the active field.
- `Enter` submits credentials.
- `Esc` exits.
- Printable letters such as `R`, `r`, `Q`, and `q` are always treated as credential input.

The mode switch deliberately does not use a printable character.

## Room menu

`RoomScreenRenderer` owns all room-menu drawing. `LobbyScreen` owns input routing and calls:

```text
RemoteGameClient.join_queue
RemoteGameClient.leave_queue
RemoteGameClient.create_room
RemoteGameClient.join_room
RemoteGameClient.leave_room
```

The room menu supports buttons and keyboard actions. Room IDs are normalized by the client and validated by the server.

## Player versus spectator UI

For White/Black, `NetworkGameApp` registers `MouseHandler` with the existing controller.

For Spectator:

- `MouseHandler` is not registered.
- The account overlay displays `SPECTATOR`.
- `RemoteGameClient.send_command` rejects commands.
- The server independently enforces `spectator_read_only`.

The spectator still receives and renders the same authoritative snapshots as both players.

## Render flow

```text
GameServer snapshot JSON
  -> RemoteGameClient sequence validation
  -> snapshot_deserializer
  -> RemoteEngine.snapshot
  -> GameScene.render
  -> OpenCV frame
```

`RemoteGameClient` ignores snapshots for a different game ID and ignores sequences older than or equal to the last accepted sequence.

## Input flow

```text
OpenCV mouse event
  -> MouseHandler
  -> Controller
  -> RemoteEngine
  -> RemoteGameClient.send_command
  -> WebSocket
  -> server authorization
  -> GameEngine
```

The local selected cell is view-only state and is not part of the authoritative server snapshot.

## Network resilience presentation

During reconnect, the client displays a connection-loss overlay while retrying with configurable exponential backoff.

When an opponent disconnects, players and spectators see the server-provided countdown. A successful reconnect clears it; expiration produces a technical-forfeit result.

If the OpenCV window is closed and a new client is opened during the grace period, the user signs in normally. The server returns `reconnect_success`, `LoginScreen` accepts the restored `PLAYING`/`SPECTATING` state, and `NetworkGameApp` skips the lobby. Quick Play is only for new matches.

## Game-over rendering

`OverlayRenderer.draw_match_result` owns the final result drawing. It displays:

```text
GAME OVER
<username> | <WHITE/BLACK> | WINS
```

or `DRAW`.

The winner identity comes from the authoritative `game_result` event. A final snapshot is applied after the result so the displayed board reflects completed captures.

## Client logging

Each OpenCV client owns a separate rotating log file under the configured client-log directory. The client records lifecycle, room, role, state, reconnect, result, and error events without credentials or tokens.

## Local launcher

`start_local_match.py` starts one server and a configurable number of clients:

```text
player_capacity + local_spectator_windows
```

The default is three windows: two potential players and one spectator client. Actual roles are always determined by room join order, not process launch order.

## SRP boundaries

| Layer | Must not do |
| --- | --- |
| Renderers | Send network messages, mutate the board, or decide permissions. |
| `net_app.py` | Contain screen logic or hard-coded layout values; it is an entry point only. |
| Screens | Calculate ELO, access SQL, validate chess moves, or draw unrelated screens. |
| `RemoteGameClient` | Draw OpenCV elements or decide chess legality. |
| `RemoteEngine` | Advance authoritative time or persist state. |
| Server | Import OpenCV or depend on UI assets. |
