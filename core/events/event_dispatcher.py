"""
Omnix V5 - Event Dispatcher

High-level event dispatching utilities for the Omnix V5 event system.

The EventDispatcher sits above EventBus and provides a stable API for
subsystems to emit normalized events without needing to know the exact
implementation details of the event bus.

Responsibilities:
    - Create standardized Omnix events
    - Normalize event names and metadata
    - Dispatch through compatible EventBus APIs
    - Support synchronous and asynchronous handlers
    - Preserve compatibility with legacy event flows

This module intentionally does not own subscriptions. Subscription
management belongs to EventBus and EventSubscriber.
"""

from __future__ import annotations

import asyncio
import inspect

from typing import Any, Dict, Optional

from .event_types import (
    EventCategory,
    EventPriority,
    EventType,
    OmnixEvent,
    create_event,
)


class EventDispatcher:
    """
    High-level dispatcher for Omnix events.

    The dispatcher accepts an EventBus-like object. The bus may expose
    one of several common APIs:

        emit(...)
        publish(...)
        dispatch(...)

    This flexibility helps Omnix V5 work with the current EventBus and
    legacy-compatible implementations.

    Example:

        dispatcher = EventDispatcher(event_bus)

        dispatcher.emit(
            EventType.SKILL_STARTED,
            source="skills_service",
            data={"skill": "browser"},
        )
    """

    def __init__(
        self,
        event_bus: Optional[Any] = None,
        *,
        default_source: str = "core",
    ) -> None:

        self._event_bus = event_bus

        self._default_source = self._normalize_source(default_source)

    # ====================================================================
    # EVENT BUS
    # ====================================================================

    def set_event_bus(
        self,
        event_bus: Any,
    ) -> None:
        """
        Set or replace the underlying event bus.
        """

        self._event_bus = event_bus

    def get_event_bus(
        self,
    ) -> Optional[Any]:
        """
        Return the configured event bus.
        """

        return self._event_bus

    @property
    def event_bus(
        self,
    ) -> Optional[Any]:

        return self._event_bus

    @property
    def default_source(
        self,
    ) -> str:

        return self._default_source

    # ====================================================================
    # MAIN DISPATCH METHODS
    # ====================================================================

    def emit(
        self,
        event_type: EventType | str,
        *,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        category: Optional[EventCategory | str] = None,
        priority: EventPriority | str = (EventPriority.NORMAL),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OmnixEvent:
        """
        Create and dispatch an Omnix event.

        Returns the normalized event object.

        If no event bus is configured, the event is still created and
        returned. This allows components to operate safely during
        initialization or standalone testing.
        """

        event = self.create(
            event_type,
            source=source,
            data=data,
            category=category,
            priority=priority,
            metadata=metadata,
        )

        self.dispatch_event(event)

        return event

    def dispatch_event(
        self,
        event: OmnixEvent,
    ) -> Any:
        """
        Dispatch an existing OmnixEvent.

        The method attempts to use a compatible API from the configured
        EventBus.
        """

        if not isinstance(
            event,
            OmnixEvent,
        ):

            raise TypeError("event must be an OmnixEvent.")

        if self._event_bus is None:

            return None

        return self._dispatch_to_bus(event)

    def create(
        self,
        event_type: EventType | str,
        *,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        category: Optional[EventCategory | str] = None,
        priority: EventPriority | str = (EventPriority.NORMAL),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OmnixEvent:
        """
        Create a normalized OmnixEvent without dispatching it.
        """

        resolved_source = (
            self._normalize_source(source)
            if source is not None
            else self._default_source
        )

        return create_event(
            event_type,
            source=resolved_source,
            data=data,
            category=category,
            priority=priority,
            metadata=metadata,
        )

    # ====================================================================
    # CONVENIENCE METHODS
    # ====================================================================

    def emit_system(
        self,
        event_type: EventType | str,
        *,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority | str = (EventPriority.NORMAL),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OmnixEvent:
        """
        Emit a system event.
        """

        return self.emit(
            event_type,
            source=source,
            data=data,
            category=EventCategory.SYSTEM,
            priority=priority,
            metadata=metadata,
        )

    def emit_service(
        self,
        event_type: EventType | str,
        *,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority | str = (EventPriority.NORMAL),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OmnixEvent:
        """
        Emit a service-related event.
        """

        return self.emit(
            event_type,
            source=source,
            data=data,
            category=EventCategory.SERVICE,
            priority=priority,
            metadata=metadata,
        )

    def emit_error(
        self,
        error: Any,
        *,
        source: Optional[str] = None,
        event_type: EventType | str = (EventType.ERROR_OCCURRED),
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        priority: EventPriority | str = (EventPriority.HIGH),
    ) -> OmnixEvent:
        """
        Emit a standardized error event.
        """

        event_data = dict(data or {})

        event_data.setdefault(
            "error",
            str(error),
        )

        event_data.setdefault(
            "error_type",
            type(error).__name__,
        )

        return self.emit(
            event_type,
            source=source,
            data=event_data,
            category=EventCategory.ERROR,
            priority=priority,
            metadata=metadata,
        )

    # ====================================================================
    # BUS COMPATIBILITY
    # ====================================================================

    def _dispatch_to_bus(
        self,
        event: OmnixEvent,
    ) -> Any:
        """
        Dispatch the event using the first compatible bus method.

        Supported methods:

            emit(event)
            publish(event)
            dispatch(event)

        The dispatcher also supports buses that expect:

            emit(event_type, event)
            emit(event_type, data)
        """

        bus = self._event_bus

        for method_name in (
            "emit",
            "publish",
            "dispatch",
        ):

            method = getattr(
                bus,
                method_name,
                None,
            )

            if not callable(method):

                continue

            return self._call_bus_method(
                method,
                event,
            )

        raise RuntimeError(
            "Configured event bus does not "
            "provide a supported dispatch method. "
            "Expected emit(), publish(), or dispatch()."
        )

    def _call_bus_method(
        self,
        method: Any,
        event: OmnixEvent,
    ) -> Any:
        """
        Call an EventBus method using a compatible signature.
        """

        try:

            result = method(event)

        except TypeError:

            try:

                result = method(
                    event.name,
                    event,
                )

            except TypeError:

                result = method(
                    event.name,
                    event.data,
                )

        return self._resolve_result(result)

    @staticmethod
    def _resolve_result(
        result: Any,
    ) -> Any:
        """
        Resolve awaitable results when possible.

        For normal synchronous Omnix execution this allows async-aware
        event buses to work without exposing unnecessary complexity to
        every subsystem.

        If an event loop is already running, the awaitable is returned
        so the caller can await it.
        """

        if not inspect.isawaitable(result):

            return result

        try:

            asyncio.get_running_loop()

        except RuntimeError:

            return asyncio.run(result)

        return result

    # ====================================================================
    # NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_source(
        source: Any,
    ) -> str:
        """
        Normalize an event source name.
        """

        value = str(source).strip()

        if not value:

            return "unknown"

        return value


# ============================================================================
# GLOBAL DISPATCHER
# ============================================================================


_default_event_dispatcher = EventDispatcher()


def get_event_dispatcher() -> EventDispatcher:
    """
    Return the shared Omnix event dispatcher.
    """

    return _default_event_dispatcher


def set_event_bus(
    event_bus: Any,
) -> None:
    """
    Configure the shared dispatcher with an EventBus.
    """

    _default_event_dispatcher.set_event_bus(event_bus)


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "EventDispatcher",
    "get_event_dispatcher",
    "set_event_bus",
]
