"""
Omnix V5
Process Model

Represents a running operating system process.
"""

from __future__ import annotations
from system.models.base_model import BaseModel
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(
    slots=True,
    kw_only=True,
)
class Process(BaseModel):
    """
    Represents a system process.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    pid: int
    name: str

    # ---------------------------------------------------------
    # Executable
    # ---------------------------------------------------------

    executable: str | None = None
    status: str = "unknown"
    command_line: list[str] = field(default_factory=list)
    working_directory: str | None = None

    # ---------------------------------------------------------
    # Parent Process
    # ---------------------------------------------------------

    parent_pid: int | None = None

    # ---------------------------------------------------------
    # Owner
    # ---------------------------------------------------------

    username: str | None = None

    # ---------------------------------------------------------
    # Runtime
    # ---------------------------------------------------------

    started_at: datetime | None = None

    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0

    thread_count: int = 0

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    running: bool = True
    suspended: bool = False
    responding: bool = True

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def executable_path(self) -> Path | None:
        """
        Returns executable as Path object.
        """

        if not self.executable:
            return None

        return Path(self.executable)

    @property
    def executable_exists(self) -> bool:
        """
        Checks if executable still exists.
        """

        path = self.executable_path

        return path.exists() if path else False

    @property
    def uptime_seconds(self) -> float:
        """
        Returns process uptime.
        """

        if self.started_at is None:
            return 0.0

        return (datetime.now() - self.started_at).total_seconds()

    @property
    def is_alive(self) -> bool:
        """
        Returns True if process is alive.
        """

        return self.running and self.responding

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def update_usage(
        self,
        cpu_percent: float,
        memory_mb: float,
    ) -> None:
        """
        Updates runtime resource usage.
        """

        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb

    def terminate(self) -> None:
        """
        Marks process as terminated.
        """

        self.running = False
        self.responding = False

    def suspend(self) -> None:
        """
        Marks process as suspended.
        """

        self.suspended = True

    def resume(self) -> None:
        """
        Marks process as resumed.
        """

        self.suspended = False

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __str__(self) -> str:

        state = "Running" if self.running else "Stopped"

        return f"{self.name} " f"(PID={self.pid}, {state})"

    def __repr__(self) -> str:

        return (
            f"Process("
            f"pid={self.pid}, "
            f"name={self.name!r}, "
            f"running={self.running}"
            f")"
        )
