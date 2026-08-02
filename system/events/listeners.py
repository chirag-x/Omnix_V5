"""
Omnix V5
Listeners

Base interfaces for event listeners.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .system_events import SystemEvent


class EventListener(ABC):
    """
    Base interface for all event listeners.
    """

    @abstractmethod
    def handle(
        self,
        event: SystemEvent,
    ) -> None:
        """
        Process an event.
        """
        raise NotImplementedError


class FunctionListener(EventListener):
    """
    Wraps a callable as an EventListener.
    """

    def __init__(
        self,
        callback,
    ) -> None:

        self._callback = callback

    def handle(
        self,
        event: SystemEvent,
    ) -> None:

        self._callback(
            event,
        )

    def __repr__(
        self,
    ) -> str:

        return "FunctionListener(" f"{self._callback.__name__})"
