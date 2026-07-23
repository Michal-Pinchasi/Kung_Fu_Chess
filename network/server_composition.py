"""Construction of multiplayer server services and handlers."""

from dataclasses import dataclass

from matchmaking.matchmaking_manager import MatchmakingManager
from network.authentication_handler import AuthenticationHandler
from network.connection_lifecycle_handler import ConnectionLifecycleHandler
from network.disconnect_manager import DisconnectManager
from network.game_command_handler import GameCommandHandler
from network.game_lifecycle_coordinator import GameLifecycleCoordinator
from network.game_registry import GameRegistry
from network.game_result_coordinator import GameResultCoordinator
from network.matchmaking_handler import MatchmakingHandler
from network.message_sender import MessageSender
from network.room_action_handler import RoomActionHandler
from observability.game_event_auditor import GameEventAuditor
from observability.logging_service import LoggingService
from rooms.room_manager import RoomManager
from services.auth_service import AuthService
from services.elo_calculator import EloCalculator
from services.game_result_service import GameResultService
from storage.user_repository import UserRepository

_DEFAULT_BOARD = """\
wR wN wB wQ wK wB wN wR
wP wP wP wP wP wP wP wP
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
bP bP bP bP bP bP bP bP
bR bN bB bQ bK bB bN bR"""


@dataclass(frozen=True)
class ServerComponents:
    """Objects composed once and consumed by the WebSocket host."""

    repository: object
    auth: object
    results: object
    matchmaking: object
    logger: object
    log_event: object
    games: object
    rooms: object
    disconnects: object
    sender: object
    authentication: object
    matchmaking_handler: object
    room_actions: object
    commands: object
    connection_lifecycle: object
    lifecycle: object


def build_server_components(settings, repository=None) -> ServerComponents:
    """Builds and wires the server dependency graph."""
    repository = repository or UserRepository(settings.database_path)
    repository.initialize()
    auth = AuthService(repository, settings)
    results = GameResultService(repository, EloCalculator(settings.elo))
    matchmaking = MatchmakingManager(
        settings.matchmaking.elo_range,
        settings.matchmaking.queue_timeout_seconds,
    )
    logging_service = LoggingService(settings.logging)
    logger = logging_service.create_logger(
        "kung_fu_chess.server", settings.logging.server_log_path
    )
    log_event = logging_service.event
    games = GameRegistry(
        _DEFAULT_BOARD, event_auditor=GameEventAuditor(logger, log_event)
    )
    rooms = RoomManager(settings.rooms)
    disconnects = DisconnectManager(settings.disconnect.grace_period_seconds)
    sender = MessageSender(logger, log_event)
    result_coordinator = GameResultCoordinator(
        games, rooms, disconnects, results, sender, logger, log_event
    )
    connection_lifecycle = ConnectionLifecycleHandler(
        games,
        rooms,
        disconnects,
        settings.disconnect.grace_period_seconds,
        result_coordinator,
        sender,
        logger,
        log_event,
    )
    lifecycle = GameLifecycleCoordinator(
        games,
        rooms,
        matchmaking,
        result_coordinator,
        connection_lifecycle,
        sender,
        logger,
        log_event,
    )
    authentication = AuthenticationHandler(
        auth, games, rooms, disconnects, sender, logger, log_event
    )
    matchmaking_handler = MatchmakingHandler(
        matchmaking, rooms, settings, lifecycle, sender, logger, log_event
    )
    room_actions = RoomActionHandler(
        matchmaking, rooms, lifecycle, sender, logger, log_event
    )
    commands = GameCommandHandler(games, rooms, sender, logger, log_event)
    return ServerComponents(
        repository,
        auth,
        results,
        matchmaking,
        logger,
        log_event,
        games,
        rooms,
        disconnects,
        sender,
        authentication,
        matchmaking_handler,
        room_actions,
        commands,
        connection_lifecycle,
        lifecycle,
    )
