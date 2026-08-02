"""
Omnix V5
Application Runtime State Model

Represents the live runtime state of an application.

This model is updated by:
- Application Monitor
- Process Manager
- Launch Strategy
- System Manager
"""

from __future__ import annotations
from system.models.base_model import BaseModel
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(
    slots=True,
    kw_only=True,
)
class ApplicationState(BaseModel):
    """
    Runtime state of an application.
    """

    # ---------------------------------------------------------
    # Process Information
    # ---------------------------------------------------------

    running: bool = False
    process_id: int | None = None
    process_name: str | None = None

    # ---------------------------------------------------------
    # Window Information
    # ---------------------------------------------------------

    window_title: str | None = None
    window_handle: int | None = None

    # ---------------------------------------------------------
    # Resource Usage
    # ---------------------------------------------------------

    cpu_percent: float = 0.0
    memory_mb: float = 0.0

    # ---------------------------------------------------------
    # Runtime
    # ---------------------------------------------------------

    started_at: datetime | None = None
    last_seen: datetime | None = None

    # ---------------------------------------------------------
    # Launch Statistics
    # ---------------------------------------------------------

    launch_count: int = 0
    crash_count: int = 0

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    responding: bool = True
    minimized: bool = False
    maximized: bool = False
    focused: bool = False

    # ---------------------------------------------------------
    # Custom Metadata
    # ---------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def mark_started(self, pid: int | None = None) -> None:
        """Mark application as started."""

        self.running = True
        self.process_id = pid
        self.started_at = datetime.now()
        self.last_seen = self.started_at
        self.launch_count += 1

    def mark_stopped(self) -> None:
        """Mark application as stopped."""

        self.running = False
        self.process_id = None
        self.focused = False

    def mark_seen(self) -> None:
        """Update last seen timestamp."""

        self.last_seen = datetime.now()

    def mark_crashed(self) -> None:
        """Record an application crash."""

        self.running = False
        self.crash_count += 1

    @property
    def uptime_seconds(self) -> float:
        """
        Returns application uptime in seconds.
        """

        if self.started_at is None:
            return 0.0

        return (datetime.now() - self.started_at).total_seconds()

    @property
    def is_alive(self) -> bool:
        """
        True if the application is running and responding.
        """

        return self.running and self.responding

    def reset(self) -> None:
        """
        Reset runtime state.
        """

        self.running = False
        self.process_id = None
        self.process_name = None
        self.window_title = None
        self.window_handle = None
        self.cpu_percent = 0.0
        self.memory_mb = 0.0
        self.started_at = None
        self.last_seen = None
        self.responding = True
        self.minimized = False
        self.maximized = False
        self.focused = False
        self.metadata.clear()

    def __str__(self) -> str:

        if self.running:
            return (
                f"Running "
                f"(PID={self.process_id}, "
                f"CPU={self.cpu_percent:.1f}%, "
                f"RAM={self.memory_mb:.1f} MB)"
            )

        return "Stopped"