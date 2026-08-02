"""
Omnix V5
Event Dispatcher

Dispatches events to registered listeners.
"""

from __future__ import annotations

import logging

from .listeners import EventListener
from .system_events import SystemEvent

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Dispatches events to listeners.

    Responsible only for invoking listeners.
    It does not manage subscriptions.
    """

    def __init__(
        self,
    ) -> None:

        self._enabled = True

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
    # Dispatch
    # ---------------------------------------------------------

    def dispatch(
        self,
        event: SystemEvent,
        listeners: list[EventListener],
    ) -> None:

        if not self._enabled:

            return

        logger.debug(

            "Dispatching %s to %d listener(s)",

            event.name,

            len(listeners),

        )

        for listener in listeners:

            try:

                listener.handle(
                    event,
                )

            except Exception:

                logger.exception(

                    "Listener %s failed while handling %s",

                    listener,

                    event.name,

                )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {

            "enabled": self._enabled,

        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return (

            "EventDispatcher("

            f"enabled={self._enabled})"

        )