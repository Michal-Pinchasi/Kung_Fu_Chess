from events.message_bus import MessageBus


def test_publish_calls_subscribed_handler_with_payload():
    bus = MessageBus()
    received = []

    bus.subscribe("thing_happened", lambda payload: received.append(payload))
    bus.publish("thing_happened", {"value": 42})

    assert received == [{"value": 42}]


def test_publish_with_no_subscribers_is_a_safe_no_op():
    bus = MessageBus()

    bus.publish("nobody_listening")  # must not raise


def test_publish_with_no_payload_defaults_to_none():
    bus = MessageBus()
    received = []

    bus.subscribe("event", lambda payload: received.append(payload))
    bus.publish("event")

    assert received == [None]


def test_multiple_handlers_all_receive_the_event():
    bus = MessageBus()
    received_a = []
    received_b = []

    bus.subscribe("event", lambda payload: received_a.append(payload))
    bus.subscribe("event", lambda payload: received_b.append(payload))
    bus.publish("event", "hello")

    assert received_a == ["hello"]
    assert received_b == ["hello"]


def test_handlers_are_called_in_subscription_order():
    bus = MessageBus()
    call_order = []

    bus.subscribe("event", lambda payload: call_order.append("first"))
    bus.subscribe("event", lambda payload: call_order.append("second"))
    bus.publish("event")

    assert call_order == ["first", "second"]


def test_subscribers_to_a_different_event_type_are_not_called():
    bus = MessageBus()
    received = []

    bus.subscribe("event_a", lambda payload: received.append(payload))
    bus.publish("event_b", "should not arrive")

    assert received == []


def test_unsubscribe_stops_further_calls():
    bus = MessageBus()
    received = []
    handler = lambda payload: received.append(payload)

    bus.subscribe("event", handler)
    bus.publish("event", 1)
    bus.unsubscribe("event", handler)
    bus.publish("event", 2)

    assert received == [1]


def test_unsubscribe_unknown_handler_is_a_safe_no_op():
    bus = MessageBus()

    bus.unsubscribe("never_subscribed", lambda payload: None)  # must not raise


def test_same_handler_can_subscribe_to_multiple_event_types():
    bus = MessageBus()
    received = []
    handler = lambda payload: received.append(payload)

    bus.subscribe("event_a", handler)
    bus.subscribe("event_b", handler)
    bus.publish("event_a", "a")
    bus.publish("event_b", "b")

    assert received == ["a", "b"]
