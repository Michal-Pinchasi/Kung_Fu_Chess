# Server Architecture - Kung Fu Chess (Phases 1-5)

## Purpose

The WebSocket server is the only authority for authentication, rooms, roles, game state, timing, legality, results, statistics, and ELO. Clients render snapshots and submit intentions; they never mutate authoritative state.

## Composition

```text
GameServer
|-- UserRepository (SQLite persistence)
|-- AuthService (registration, verification, session tokens)
|-- MatchmakingManager (rating queue and timeout)
|-- RoomManager (room registry and membership indexes)
|   `-- GameRoom (roles, occupants, room state)
|-- GameRegistry (game registry and user indexes)
|   `-- GameSession (one GameEngine and two player slots)
|-- DisconnectManager (grace-period deadlines)
|-- GameResultService + EloCalculator
`-- LoggingService + GameEventAuditor
```

## Responsibility boundaries

| Component | Responsibility |
| --- | --- |
| `network/websocket_server.py` | Protocol routing and dependency composition. |
| `rooms/room_manager.py` | Secure room creation and indexed lookup. |
| `rooms/game_room.py` | Membership, roles, connections, and room state. |
| `matchmaking/matchmaking_manager.py` | Rating-aware queue, pairing, leave, and timeout. |
| `network/game_registry.py` | Creation and lookup of independent game sessions. |
| `network/game_session.py` | Runtime and authorization for one match. |
| `network/disconnect_manager.py` | Grace-period countdown state only. |
| `services/auth_service.py` | Password verification and session-token ownership. |
| `storage/user_repository.py` | SQL and transactional user/statistics persistence. |
| `services/elo_calculator.py` | Pure configurable ELO mathematics. |
| `services/game_result_service.py` | Coordinate one persisted result. |
| `observability/logging_service.py` | Rotating logging and sensitive-data filtering. |
| `observability/game_event_auditor.py` | Bridge MessageBus events into audit logs. |

## Authentication flow

```text
auth(register/login)
  -> AuthService
  -> PBKDF2 verification
  -> server-owned User
  -> auth_result (username, rating, token)
  -> lobby_ready
```

Credentials and tokens are never logged. The server derives identity and rating from the authenticated user rather than client claims.

## Quick Play flow

```text
join_queue
  -> MatchmakingManager.join
  -> rating/time ordered search
  -> mutual configured ELO window
  -> RoomManager.create_for_match
  -> GameRegistry.create
  -> match_found + initial snapshot
```

An unmatched entry expires after the configured timeout and receives `matchmaking_timeout`.

## Private room flow

```text
create_room
  -> secure Room ID
  -> creator receives White

join_room(room_id)
  -> second member receives Black
  -> game starts
  -> later members receive Spectator
```

Room roles are assigned only by the server. A spectator command is rejected before it reaches `GameEngine`.

## Game and snapshot flow

Each match owns an independent `GameEngine`, board, MessageBus, sequence counter, and result guard.

```text
tick loop
  -> GameSession.tick
  -> GameEngine.wait
  -> GameSession.next_snapshot
  -> serialize(game_id, sequence, state)
  -> broadcast to every connected GameRoom member
```

Clients discard snapshots whose sequence is not newer than their last accepted sequence.

## Disconnect and reconnect flow

Player disconnect:

```text
GameRoom.disconnect
  -> GameSession.disconnect
  -> DisconnectManager.start
  -> countdown to opponent and spectators
```

Reconnect validates the session token, game ID, room membership, stored role, and grace deadline. Success replaces the socket, cancels the deadline, and sends the latest authoritative snapshot.

After a fresh client Login, `AuthenticationHandler` also checks the authenticated user's indexed game and disconnected room member. If the grace deadline is still active, it restores the new socket automatically and skips the lobby.

Grace expiration calls the normal result path with `technical_forfeit`. `result_applied` ensures database statistics and ELO are updated once. Before clients receive the result, the game, room, user, and disconnect indexes are released so the next Quick Play request cannot race with cleanup.

A spectator disconnect does not start a forfeit deadline and does not affect the game.

## Game-over consistency

When a moving piece is captured, `RealTimeArbiter.cancel_piece_activities` removes its pending move/jump/rest. A captured king therefore cannot land later and reappear.

The winner is derived from the captured king color in the resolving tick. After `game_result`, the server broadcasts an authoritative final snapshot so clients never remain on an in-flight frame.

## WebSocket messages

Client to server:

```text
auth
join_queue
leave_queue
create_room
join_room
leave_room
reconnect
Move command
Jump command
```

Server to client:

```text
auth_result / auth_error
lobby_ready
queue_joined / queue_left / matchmaking_timeout / matchmaking_error
room_created / room_joined / room_left / room_state / room_error
match_found
snapshot
opponent_disconnected / opponent_reconnected
reconnect_success
game_result
error
```

## Logging and auditing

Server and client loggers use rotating files. The server audits connection lifecycle, authentication outcome, queue operations, room creation/join, role assignment, accepted commands, rejected spectator commands, disconnect/reconnect, game results, and MessageBus events.

`SensitiveDataFilter` recursively redacts password, hash, salt, token, session-token, and authorization fields before disk output.

## Verification

The automated non-interactive suite currently reports:

```text
233 passed, 1 skipped
```
