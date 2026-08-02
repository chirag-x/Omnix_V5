"""
Omnix V5
Event Bus

Central publish/subscribe event system.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from .listeners import EventListener
from .system_events import SystemEvent
from .event_dispatcher import EventDispatcher

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event bus.

    Manages event subscriptions and publishing.
    """

    def __init__(
        self,
    ) -> None:

        self._listeners: dict[
            str,
            list[EventListener],
        ] = defaultdict(
            list,
        )

        self._enabled = True
        self._dispatcher = EventDispatcher()

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def enabled(
        self,
    ) -> bool:

        return self._enabled

    def enable(
        self,
    ) -> None:

        self._enabled = True

    def disable(
        self,
    ) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Subscription
    # ---------------------------------------------------------

    def subscribe(
        self,
        event_name: str,
        listener: EventListener,
    ) -> None:

        if listener not in self._listeners[event_name]:

            self._listeners[event_name].append(
                listener,
            )

            logger.debug(
                "Subscribed %s to %s",
                listener,
                event_name,
            )

    def unsubscribe(
        self,
        event_name: str,
        listener: EventListener,
    ) -> None:

        listeners = self._listeners.get(
            event_name,
        )

        if not listeners:

            return

        if listener in listeners:

            listeners.remove(
                listener,
            )

            logger.debug(
                "Unsubscribed %s from %s",
                listener,
                event_name,
            )

    # ---------------------------------------------------------
    # Publishing
    # ---------------------------------------------------------

    def publish(
        self,
        event: SystemEvent,
    ) -> None:

        if not self._enabled:

            return

        listeners = self._listeners.get(
            event.name,
            [],
        )

        logger.debug(
            "Publishing %s to %d listener(s)",
            event.name,
            len(listeners),
        )

        self._dispatcher.dispatch(
            event,
            listeners,
        )

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def clear(
        self,
    ) -> None:

        self._listeners.clear()

    @property
    def listener_count(
        self,
    ) -> int:

        return sum(len(listeners) for listeners in self._listeners.values())

    @property
    def event_count(
        self,
    ) -> int:

        return len(
            self._listeners,
        )

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
            "events": self.event_count,
            "listeners": self.listener_count,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return (
            "EventBus("
            f"events={self.event_count}, "
            f"listeners={self.listener_count}, "
            f"enabled={self._enabled})"
        )
