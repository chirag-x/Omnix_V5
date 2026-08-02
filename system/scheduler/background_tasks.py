"""
Omnix V5
Background Tasks

Represents a background task managed by the scheduler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass(slots=True)
class BackgroundTask:
    """
    Represents a scheduled background task.
    """

    name: str

    callback: Callable[..., Any]

    interval: float = 0.0

    repeat: bool = False

    enabled: bool = True

    last_run: datetime | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    def execute(
        self,
    ) -> Any:
        """
        Execute the background task.
        """

        self.last_run = datetime.utcnow()

        return self.callback()

    def enable(
        self,
    ) -> None:

        self.enabled = True

    def disable(
        self,
    ) -> None:

        self.enabled = False

    @property
    def has_run(
        self,
    ) -> bool:

        return self.last_run is not None

    def statistics(
        self,
    ) -> dict:

        return {
            "name": self.name,
            "enabled": self.enabled,
            "repeat": self.repeat,
            "interval": self.interval,
            "has_run": self.has_run,
        }

    def __repr__(
        self,
    ) -> str:

        return (
            "BackgroundTask("
            f"name='{self.name}', "
            f"repeat={self.repeat}, "
            f"enabled={self.enabled})"
        )
