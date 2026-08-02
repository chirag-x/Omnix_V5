"""
Omnix V5
Timers

Utility timer classes for scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass(slots=True)
class Timer:
    """
    Represents a simple timer.
    """

    interval: float

    repeat: bool = False

    started_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    def expired(self) -> bool:
        """
        Returns True if the timer has elapsed.
        """
        return datetime.utcnow() >= (self.started_at + timedelta(seconds=self.interval))

    def reset(self) -> None:
        """
        Restart the timer.
        """
        self.started_at = datetime.utcnow()

    def remaining(self) -> float:
        """
        Seconds remaining until expiration.
        """
        end = self.started_at + timedelta(seconds=self.interval)
        return max(
            0.0,
            (end - datetime.utcnow()).total_seconds(),
        )

    def __repr__(self) -> str:
        return "Timer(" f"interval={self.interval}, " f"repeat={self.repeat})"
