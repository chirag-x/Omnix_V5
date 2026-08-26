"""
Omnix V5 - Event Bus

Central event communication system for Omnix V5.

This module allows subsystems to communicate without
directly depending on each other.

Example:

    event_bus.subscribe(
        "vision.object_detected",
        on_object_detected,
    )

    event_bus.publish(
        "vision.object_detected",
        object_name="person",
        confidence=0.94,
    )

Features:
    - Named events
    - Wildcard subscriptions
    - Priority-based listeners
    - One-time listeners
    - Safe listener execution
    - Event history
    - Listener management
    - Legacy callback compatibility
    - Thread-safe operations
"""

from __future__ import annotations

import inspect
import logging
import threading
import time
import uuid

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("omnix.core.event_bus")


# ============================================================================
# EXCEPTIONS
# ============================================================================


class EventBusError(Exception):
    """Base exception for EventBus errors."""


class EventNotFoundError(EventBusError):
    """Raised when an event operation is invalid."""


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Event:
    """
    Represents an Omnix event.
    """

    name: str

    data: Dict[str, Any] = field(default_factory=dict)

    source: Optional[str] = None

    timestamp: float = field(default_factory=time.time)

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a value from event data."""

        return self.data.get(
            key,
            default,
        )

    def __getitem__(
        self,
        key: str,
    ) -> Any:
        """Allow event['key'] access."""

        return self.data[key]


@dataclass
class EventListener:
    """
    Registered event listener.
    """

    listener_id: str

    event_name: str

    callback: Callable[..., Any]

    priority: int = 100

    once: bool = False

    enabled: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventListenerResult:
    """
    Result of one listener execution.
    """

    listener_id: str

    success: bool

    value: Any = None

    error: Optional[str] = None

    duration: float = 0.0


@dataclass
class EventResult:
    """
    Result of publishing an event.
    """

    event: Event

    success: bool = True

    listener_results: List[EventListenerResult] = field(default_factory=list)

    errors: Dict[str, str] = field(default_factory=dict)

    duration: float = 0.0

    @property
    def executed_count(self) -> int:
        """Number of successfully executed listeners."""

        return sum(1 for result in self.listener_results if result.success)

    @property
    def failed_count(self) -> int:
        """Number of failed listeners."""

        return sum(1 for result in self.listener_results if not result.success)


# ============================================================================
# EVENT BUS
# ============================================================================


class EventBus:
    """
    Thread-safe event bus for Omnix V5.

    Event naming convention:

        subsystem.action

    Examples:

        system.started
        system.stopping

        vision.frame_processed
        vision.object_detected

        skills.started
        skills.completed
        skills.failed

        agent.task_started
        agent.task_completed
        agent.task_failed

        memory.updated

        ui.notification

    Wildcards:

        "*"
            Receives every event.

        "vision.*"
            Receives all vision events.

        "skills.*"
            Receives all skill events.
    """

    def __init__(
        self,
        *,
        history_limit: int = 500,
    ) -> None:

        self._listeners: Dict[str, List[EventListener]] = {}

        self._listener_index: Dict[str, EventListener] = {}

        self._history: List[Event] = []

        self._history_limit = max(
            1,
            history_limit,
        )

        self._lock = threading.RLock()

        self._started_at = time.time()

        logger.debug("EventBus initialized")

    # ========================================================================
    # SUBSCRIPTIONS
    # ========================================================================

    def subscribe(
        self,
        event_name: str,
        callback: Callable[..., Any],
        *,
        priority: int = 100,
        once: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Subscribe a callback to an event.

        Returns a listener ID that can later be used
        with unsubscribe().

        Example:

            listener_id = event_bus.subscribe(
                "vision.object_detected",
                callback,
            )
        """

        event_name = self._normalize_event_name(event_name)

        if not callable(callback):
            raise TypeError("Event callback must be callable.")

        listener_id = str(uuid.uuid4())

        listener = EventListener(
            listener_id=listener_id,
            event_name=event_name,
            callback=callback,
            priority=priority,
            once=once,
            metadata=dict(metadata or {}),
        )

        with self._lock:

            listeners = self._listeners.setdefault(
                event_name,
                [],
            )

            listeners.append(listener)

            listeners.sort(key=lambda item: item.priority)

            self._listener_index[listener_id] = listener

        logger.debug(
            "Subscribed listener '%s' " "to event '%s'",
            listener_id,
            event_name,
        )

        return listener_id

    def once(
        self,
        event_name: str,
        callback: Callable[..., Any],
        *,
        priority: int = 100,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Subscribe a listener that runs once.
        """

        return self.subscribe(
            event_name,
            callback,
            priority=priority,
            once=True,
            metadata=metadata,
        )

    def unsubscribe(
        self,
        listener_id: str,
    ) -> bool:
        """
        Remove a listener using its listener ID.
        """

        with self._lock:

            listener = self._listener_index.pop(
                listener_id,
                None,
            )

            if listener is None:
                return False

            listeners = self._listeners.get(
                listener.event_name,
                [],
            )

            self._listeners[listener.event_name] = [
                item for item in listeners if item.listener_id != listener_id
            ]

            if not self._listeners[listener.event_name]:

                self._listeners.pop(
                    listener.event_name,
                    None,
                )

        logger.debug(
            "Unsubscribed listener '%s'",
            listener_id,
        )

        return True

    def unsubscribe_callback(
        self,
        callback: Callable[..., Any],
        event_name: Optional[str] = None,
    ) -> int:
        """
        Remove listeners associated with a callback.

        Returns number of removed listeners.
        """

        removed = 0

        with self._lock:

            listener_ids = []

            for listener_id, listener in self._listener_index.items():

                if listener.callback is not callback:
                    continue

                if event_name is not None:

                    normalized = self._normalize_event_name(event_name)

                    if listener.event_name != normalized:
                        continue

                listener_ids.append(listener_id)

        for listener_id in listener_ids:

            if self.unsubscribe(listener_id):
                removed += 1

        return removed

    # ========================================================================
    # LISTENER CONTROL
    # ========================================================================

    def enable_listener(
        self,
        listener_id: str,
        enabled: bool = True,
    ) -> bool:
        """
        Enable or disable a listener.
        """

        with self._lock:

            listener = self._listener_index.get(listener_id)

            if listener is None:
                return False

            listener.enabled = enabled

            return True

    def clear(
        self,
        event_name: Optional[str] = None,
    ) -> int:
        """
        Remove listeners.

        If event_name is None, removes all listeners.
        """

        with self._lock:

            if event_name is None:

                count = len(self._listener_index)

                self._listeners.clear()

                self._listener_index.clear()

                return count

            event_name = self._normalize_event_name(event_name)

            listeners = self._listeners.pop(
                event_name,
                [],
            )

            for listener in listeners:

                self._listener_index.pop(
                    listener.listener_id,
                    None,
                )

            return len(listeners)

    # ========================================================================
    # EVENT PUBLISHING
    # ========================================================================

    def publish(
        self,
        event_name: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = False,
        **kwargs: Any,
    ) -> EventResult:
        """
        Publish an event.

        Event data can be provided either through
        the data dictionary or keyword arguments.

        Example:

            event_bus.publish(
                "vision.object_detected",
                {
                    "object": "person",
                },
                confidence=0.95,
            )

        Both values are merged into event.data.
        """

        event_name = self._normalize_event_name(event_name)

        payload = dict(data or {})

        payload.update(kwargs)

        event = Event(
            name=event_name,
            data=payload,
            source=source,
            metadata=dict(metadata or {}),
        )

        return self.emit(
            event,
            raise_on_error=raise_on_error,
        )

    def emit(
        self,
        event: Event,
        *,
        raise_on_error: bool = False,
    ) -> EventResult:
        """
        Emit an existing Event instance.
        """

        if not isinstance(
            event,
            Event,
        ):
            raise TypeError("event must be an Event instance.")

        started_at = time.perf_counter()

        listeners = self._get_matching_listeners(event.name)

        result = EventResult(event=event)

        once_listeners: List[str] = []

        for listener in listeners:

            if not listener.enabled:
                continue

            listener_started = time.perf_counter()

            try:

                value = self._invoke_listener(
                    listener.callback,
                    event,
                )

                listener_result = EventListenerResult(
                    listener_id=(listener.listener_id),
                    success=True,
                    value=value,
                    duration=(time.perf_counter() - listener_started),
                )

            except Exception as exc:

                logger.exception(
                    "Event listener failed for " "'%s': %s",
                    event.name,
                    listener.listener_id,
                )

                listener_result = EventListenerResult(
                    listener_id=(listener.listener_id),
                    success=False,
                    error=str(exc),
                    duration=(time.perf_counter() - listener_started),
                )

                result.success = False

                result.errors[listener.listener_id] = str(exc)

                if raise_on_error:

                    result.listener_results.append(listener_result)

                    self._store_event(event)

                    raise EventBusError(
                        f"Listener " f"'{listener.listener_id}' " f"failed: {exc}"
                    ) from exc

            result.listener_results.append(listener_result)

            if listener.once:

                once_listeners.append(listener.listener_id)

        for listener_id in once_listeners:

            self.unsubscribe(listener_id)

        self._store_event(event)

        result.duration = time.perf_counter() - started_at

        return result

    # ========================================================================
    # MATCHING
    # ========================================================================

    def _get_matching_listeners(
        self,
        event_name: str,
    ) -> List[EventListener]:
        """
        Return listeners matching an event.

        Matching patterns:

            exact:
                vision.object_detected

            subsystem wildcard:
                vision.*

            global wildcard:
                *
        """

        with self._lock:

            matches: List[EventListener] = []

            exact = self._listeners.get(
                event_name,
                [],
            )

            matches.extend(exact)

            if "." in event_name:

                namespace = event_name.split(
                    ".",
                    1,
                )[0]

                wildcard_name = f"{namespace}.*"

                wildcard = self._listeners.get(
                    wildcard_name,
                    [],
                )

                matches.extend(wildcard)

            global_listeners = self._listeners.get(
                "*",
                [],
            )

            matches.extend(global_listeners)

        matches.sort(key=lambda item: item.priority)

        return matches

    # ========================================================================
    # CALLBACK INVOCATION
    # ========================================================================

    @staticmethod
    def _invoke_listener(
        callback: Callable[..., Any],
        event: Event,
    ) -> Any:
        """
        Execute an event listener.

        Supported listener signatures:

            callback()

            callback(event)

            callback(data)

            callback(event=event)

            callback(data=event.data)

            callback(event, ...)
            with optional parameters.
        """

        try:

            signature = inspect.signature(callback)

        except (
            TypeError,
            ValueError,
        ):

            result = callback(event)

            return EventBus._validate_listener_result(result)

        parameters = list(signature.parameters.values())

        positional = [
            parameter
            for parameter in parameters
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

        keyword_only = [
            parameter
            for parameter in parameters
            if parameter.kind == inspect.Parameter.KEYWORD_ONLY
        ]

        if not positional and not keyword_only:

            result = callback()

            return EventBus._validate_listener_result(result)

        kwargs: Dict[str, Any] = {}

        args: List[Any] = []

        if positional:

            first = positional[0]

            if first.name in (
                "data",
                "payload",
            ):

                args.append(event.data)

            else:

                args.append(event)

            for parameter in positional[1:]:

                if parameter.default is inspect.Parameter.empty:

                    raise EventBusError(
                        "Cannot resolve required "
                        "listener parameter "
                        f"'{parameter.name}'."
                    )

        for parameter in keyword_only:

            if parameter.name in (
                "event",
                "evt",
            ):

                kwargs[parameter.name] = event

            elif parameter.name in (
                "data",
                "payload",
            ):

                kwargs[parameter.name] = event.data

            elif parameter.default is inspect.Parameter.empty:

                raise EventBusError(
                    "Cannot resolve required "
                    "listener parameter "
                    f"'{parameter.name}'."
                )

        result = callback(
            *args,
            **kwargs,
        )

        return EventBus._validate_listener_result(result)

    @staticmethod
    def _validate_listener_result(
        result: Any,
    ) -> Any:
        """
        Validate listener output.

        Async listeners are intentionally not executed
        here. Async event execution should later be
        handled by Omnix's task/runtime layer.
        """

        if inspect.isawaitable(result):

            raise EventBusError(
                "Async event listeners are not "
                "supported by the synchronous "
                "EventBus."
            )

        return result

    # ========================================================================
    # EVENT HISTORY
    # ========================================================================

    def _store_event(
        self,
        event: Event,
    ) -> None:
        """
        Store event in history.
        """

        with self._lock:

            self._history.append(event)

            if len(self._history) > self._history_limit:

                self._history = self._history[-self._history_limit :]

    def get_history(
        self,
        *,
        event_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """
        Return event history.

        event_name supports exact matching.
        """

        with self._lock:

            events = list(self._history)

        if event_name is not None:

            normalized = self._normalize_event_name(event_name)

            events = [event for event in events if event.name == normalized]

        if limit is not None:

            limit = max(
                0,
                limit,
            )

            events = events[-limit:]

        return events

    def clear_history(
        self,
    ) -> None:
        """
        Clear stored event history.
        """

        with self._lock:

            self._history.clear()

    # ========================================================================
    # LISTENER INSPECTION
    # ========================================================================

    def get_listeners(
        self,
        event_name: Optional[str] = None,
    ) -> List[EventListener]:
        """
        Return registered listeners.
        """

        with self._lock:

            if event_name is None:

                return list(self._listener_index.values())

            event_name = self._normalize_event_name(event_name)

            return list(
                self._listeners.get(
                    event_name,
                    [],
                )
            )

    def listener_count(
        self,
        event_name: Optional[str] = None,
    ) -> int:
        """
        Return listener count.
        """

        return len(self.get_listeners(event_name))

    def event_names(
        self,
    ) -> List[str]:
        """
        Return all event patterns with listeners.
        """

        with self._lock:

            return sorted(self._listeners.keys())

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def diagnostics(
        self,
    ) -> Dict[str, Any]:
        """
        Return EventBus diagnostics.
        """

        with self._lock:

            listeners = {
                event_name: [
                    {
                        "listener_id": (listener.listener_id),
                        "priority": (listener.priority),
                        "once": (listener.once),
                        "enabled": (listener.enabled),
                        "metadata": dict(listener.metadata),
                    }
                    for listener in event_listeners
                ]
                for event_name, event_listeners in self._listeners.items()
            }

            history_count = len(self._history)

        return {
            "uptime": (time.time() - self._started_at),
            "event_pattern_count": len(listeners),
            "listener_count": self.listener_count(),
            "history_count": history_count,
            "listeners": listeners,
        }

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_event_name(
        event_name: str,
    ) -> str:
        """
        Normalize and validate an event name.
        """

        if not isinstance(
            event_name,
            str,
        ):

            raise TypeError("Event name must be a string.")

        event_name = (
            event_name.strip()
            .lower()
            .replace(
                " ",
                "_",
            )
        )

        if not event_name:

            raise ValueError("Event name cannot be empty.")

        return event_name

    # ========================================================================
    # MAGIC METHODS
    # ========================================================================

    def __contains__(
        self,
        event_name: str,
    ) -> bool:

        event_name = self._normalize_event_name(event_name)

        with self._lock:

            return event_name in self._listeners

    def __len__(
        self,
    ) -> int:

        with self._lock:

            return len(self._listener_index)

    def __repr__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}("
            f"listeners={len(self)}, "
            f"events="
            f"{len(self.event_names())}"
            f")"
        )


# ============================================================================
# DEFAULT EVENT BUS
# ============================================================================

_default_event_bus: Optional[EventBus] = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """
    Return the shared Omnix V5 EventBus instance.

    The instance is created lazily and reused by all callers unless
    a different EventBus instance is explicitly injected.
    """

    global _default_event_bus

    if _default_event_bus is not None:
        return _default_event_bus

    with _event_bus_lock:

        if _default_event_bus is None:

            _default_event_bus = EventBus()

    return _default_event_bus
