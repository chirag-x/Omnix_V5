"""
Omnix V5 - Event Subscriber

Utilities for managing event subscriptions in the Omnix V5 event system.

This module provides a reusable EventSubscriber that can:

    - Subscribe handlers to events
    - Track active subscriptions
    - Unsubscribe individual handlers
    - Unsubscribe all handlers safely
    - Support common EventBus APIs
    - Work with synchronous or asynchronous handlers
    - Preserve compatibility with legacy event buses

The EventSubscriber does not own the EventBus. It acts as a managed
subscription layer on top of the configured bus.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .event_types import EventType

# ============================================================================
# SUBSCRIPTION
# ============================================================================


@dataclass
class EventSubscription:
    """
    Represents a tracked event subscription.
    """

    event_type: str

    handler: Callable[..., Any]

    token: Optional[Any] = None

    active: bool = True


# ============================================================================
# EVENT SUBSCRIBER
# ============================================================================


class EventSubscriber:
    """
    Managed subscription helper for Omnix events.

    The class supports EventBus implementations exposing common APIs:

        subscribe(event_type, handler)
        on(event_type, handler)
        add_listener(event_type, handler)

    For removing subscriptions it supports:

        unsubscribe(...)
        off(...)
        remove_listener(...)

    Example:

        subscriber = EventSubscriber(event_bus)

        subscriber.subscribe(
            EventType.SKILL_COMPLETED,
            handle_skill_completed,
        )

        ...

        subscriber.unsubscribe_all()
    """

    def __init__(
        self,
        event_bus: Optional[Any] = None,
        *,
        name: str = "subscriber",
    ) -> None:

        self._event_bus = event_bus

        self._name = self._normalize_name(name)

        self._subscriptions: List[EventSubscription] = []

    # ====================================================================
    # EVENT BUS
    # ====================================================================

    def set_event_bus(
        self,
        event_bus: Any,
    ) -> None:
        """
        Set or replace the EventBus.

        Existing tracked subscriptions remain associated with the old bus.
        It is recommended to call unsubscribe_all() before replacing a
        live EventBus.
        """

        self._event_bus = event_bus

    def get_event_bus(
        self,
    ) -> Optional[Any]:
        """
        Return the configured EventBus.
        """

        return self._event_bus

    @property
    def event_bus(
        self,
    ) -> Optional[Any]:

        return self._event_bus

    @property
    def name(
        self,
    ) -> str:

        return self._name

    # ====================================================================
    # SUBSCRIBE
    # ====================================================================

    def subscribe(
        self,
        event_type: EventType | str,
        handler: Callable[..., Any],
    ) -> EventSubscription:
        """
        Subscribe a handler to an event.

        Returns:
            EventSubscription
        """

        if not callable(handler):

            raise TypeError("handler must be callable.")

        normalized_event_type = self._normalize_event_type(event_type)

        if self._event_bus is None:

            raise RuntimeError("No EventBus is configured.")

        token = self._subscribe_to_bus(
            normalized_event_type,
            handler,
        )

        subscription = EventSubscription(
            event_type=(normalized_event_type),
            handler=handler,
            token=token,
            active=True,
        )

        self._subscriptions.append(subscription)

        return subscription

    def subscribe_many(
        self,
        subscriptions: Dict[
            EventType | str,
            Callable[..., Any],
        ],
    ) -> List[EventSubscription]:
        """
        Subscribe multiple event handlers.

        Example:

            subscriber.subscribe_many({
                EventType.SYSTEM_STARTED:
                    on_started,

                EventType.SYSTEM_STOPPED:
                    on_stopped,
            })
        """

        if not isinstance(
            subscriptions,
            dict,
        ):

            raise TypeError("subscriptions must be a dictionary.")

        results: List[EventSubscription] = []

        for event_type, handler in subscriptions.items():

            results.append(
                self.subscribe(
                    event_type,
                    handler,
                )
            )

        return results

    # ====================================================================
    # UNSUBSCRIBE
    # ====================================================================

    def unsubscribe(
        self,
        subscription: EventSubscription,
    ) -> bool:
        """
        Unsubscribe a tracked subscription.

        Returns True if the subscription was successfully removed.
        """

        if not isinstance(
            subscription,
            EventSubscription,
        ):

            raise TypeError("subscription must be " "an EventSubscription.")

        if not subscription.active:

            return False

        success = self._unsubscribe_from_bus(subscription)

        subscription.active = False

        if subscription in self._subscriptions:

            self._subscriptions.remove(subscription)

        return success

    def unsubscribe_handler(
        self,
        event_type: EventType | str,
        handler: Callable[..., Any],
    ) -> bool:
        """
        Unsubscribe a specific handler from an event.
        """

        normalized_event_type = self._normalize_event_type(event_type)

        for subscription in list(self._subscriptions):

            if (
                subscription.event_type == normalized_event_type
                and subscription.handler is handler
            ):

                return self.unsubscribe(subscription)

        return False

    def unsubscribe_event(
        self,
        event_type: EventType | str,
    ) -> int:
        """
        Unsubscribe all tracked handlers for an event.

        Returns:
            Number of subscriptions removed.
        """

        normalized_event_type = self._normalize_event_type(event_type)

        removed = 0

        for subscription in list(self._subscriptions):

            if subscription.event_type == normalized_event_type:

                if self.unsubscribe(subscription):

                    removed += 1

        return removed

    def unsubscribe_all(
        self,
    ) -> int:
        """
        Remove all tracked subscriptions.

        Returns:
            Number of successfully removed subscriptions.
        """

        removed = 0

        for subscription in list(self._subscriptions):

            if self.unsubscribe(subscription):

                removed += 1

        return removed

    # ====================================================================
    # LOOKUP
    # ====================================================================

    def get_subscriptions(
        self,
        *,
        active_only: bool = True,
    ) -> List[EventSubscription]:
        """
        Return tracked subscriptions.
        """

        if active_only:

            return [
                subscription
                for subscription in self._subscriptions
                if subscription.active
            ]

        return list(self._subscriptions)

    def get_event_subscriptions(
        self,
        event_type: EventType | str,
    ) -> List[EventSubscription]:
        """
        Return subscriptions for one event type.
        """

        normalized_event_type = self._normalize_event_type(event_type)

        return [
            subscription
            for subscription in self._subscriptions
            if (
                subscription.event_type == normalized_event_type and subscription.active
            )
        ]

    @property
    def subscription_count(
        self,
    ) -> int:
        """
        Return number of active subscriptions.
        """

        return len(self.get_subscriptions(active_only=True))

    # ====================================================================
    # EVENT BUS COMPATIBILITY
    # ====================================================================

    def _subscribe_to_bus(
        self,
        event_type: str,
        handler: Callable[..., Any],
    ) -> Any:
        """
        Subscribe using a compatible EventBus API.
        """

        bus = self._event_bus

        for method_name in (
            "subscribe",
            "on",
            "add_listener",
        ):

            method = getattr(
                bus,
                method_name,
                None,
            )

            if not callable(method):

                continue

            return method(
                event_type,
                handler,
            )

        raise RuntimeError(
            "Configured EventBus does not "
            "provide a supported subscription method. "
            "Expected subscribe(), on(), "
            "or add_listener()."
        )

    def _unsubscribe_from_bus(
        self,
        subscription: EventSubscription,
    ) -> bool:
        """
        Unsubscribe using a compatible EventBus API.
        """

        if self._event_bus is None:

            return False

        bus = self._event_bus

        for method_name in (
            "unsubscribe",
            "off",
            "remove_listener",
        ):

            method = getattr(
                bus,
                method_name,
                None,
            )

            if not callable(method):

                continue

            try:

                result = method(
                    subscription.event_type,
                    subscription.handler,
                )

            except TypeError:

                if subscription.token is not None:

                    result = method(subscription.token)

                else:

                    raise

            if result is None:

                return True

            return bool(result)

        return False

    # ====================================================================
    # NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_event_type(
        event_type: EventType | str,
    ) -> str:
        """
        Normalize an event type.
        """

        if isinstance(
            event_type,
            EventType,
        ):

            return event_type.value

        value = str(event_type).strip()

        if not value:

            raise ValueError("event_type cannot be empty.")

        return value

    @staticmethod
    def _normalize_name(
        name: Any,
    ) -> str:
        """
        Normalize subscriber name.
        """

        value = str(name).strip()

        if not value:

            return "subscriber"

        return value


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "EventSubscription",
    "EventSubscriber",
]
