"""
A minimal synchronous publish/subscribe event bus.

Decouples event producers (e.g. GameEngine, which announces that a move
completed or the game ended) from event consumers (e.g. a WebSocket
broadcaster, a sound-effect trigger, an analytics logger) so a producer
never needs to know who — if anyone — is listening. Producers call
publish(); consumers register with subscribe() ahead of time.

The bus itself contains no threading or asyncio: publish() calls every
subscribed handler synchronously, in registration order, on the calling
thread. Consumers that need to do asynchronous work (like sending a
WebSocket message) are responsible for scheduling that work themselves
(e.g. via asyncio.create_task) inside their handler.
"""

from typing import Any, Callable, Dict, List


class MessageBus:
    """A synchronous publish/subscribe event bus keyed by event type string.

    Any number of handlers can subscribe to the same event type. Publishing
    an event type with no subscribers is a safe no-op.
    """

    def __init__(self) -> None:
        """Initialize an empty bus with no registered subscribers."""
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Register handler to be invoked whenever event_type is published.

        Parameters
        ----------
        event_type : str
            The event type to listen for (see events.game_events for the
            standard set of type constants used by GameEngine).
        handler : Callable[[Any], None]
            A callable accepting a single payload argument. The payload's
            shape depends on event_type — see events.game_events for the
            corresponding dataclass, or None if the event carries no data.
        """
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Remove a previously registered handler for event_type.

        Silently does nothing if handler was never subscribed to event_type,
        so callers don't need to guard against double-unsubscribe.
        """
        handlers = self._subscribers.get(event_type)
        if handlers is not None and handler in handlers:
            handlers.remove(handler)

    def publish(self, event_type: str, payload: Any = None) -> None:
        """Synchronously invoke every handler subscribed to event_type.

        Handlers are called in the order they were subscribed. If no
        handler is subscribed to event_type, this is a no-op — publishers
        never need to check whether anyone is listening first.
        """
        for handler in list(self._subscribers.get(event_type, [])):
            handler(payload)
