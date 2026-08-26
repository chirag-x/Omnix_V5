"""
Omnix V5 - Events Package

Central exports for the Omnix event system.

Provides:
    - Event bus
    - Event dispatcher
    - Event subscribers
    - Event types and priorities
    - Standard Omnix event objects
"""

from .event_bus import (
    EventBus,
    get_event_bus,
)

from .event_types import (
    EventCategory,
    EventPriority,
    EventType,
    OmnixEvent,
    create_event,
)

from .event_dispatcher import (
    EventDispatcher,
    get_event_dispatcher,
    set_event_bus,
)

from .event_subscriber import (
    EventSubscription,
    EventSubscriber,
)

__all__ = [
    # Event Bus
    "EventBus",
    "get_event_bus",
    # Event Types
    "EventCategory",
    "EventPriority",
    "EventType",
    "OmnixEvent",
    "create_event",
    # Event Dispatcher
    "EventDispatcher",
    "get_event_dispatcher",
    "set_event_bus",
    # Event Subscriber
    "EventSubscription",
    "EventSubscriber",
]
