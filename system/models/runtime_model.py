"""
Omnix V5
Runtime Model

Provides common runtime functionality for execution
and state-based models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


from .base_model import BaseModel


@dataclass(
    slots=True,
    kw_only=True,
)
class RuntimeModel(BaseModel):
    """
    Base class for runtime/state models.
    """

    # ---------------------------------------------------------
    # Runtime
    # ---------------------------------------------------------

    started_at: datetime | None = None

    completed_at: datetime | None = None

    execution_time: float = 0.0

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    success: bool | None = None

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return (
            self.started_at is not None
            and self.completed_at is None
        )

    @property
    def is_finished(self) -> bool:
        return self.completed_at is not None

    @property
    def duration(self) -> float:
        """
        Returns runtime in seconds.
        """

        if self.started_at is None:
            return 0.0

        end = self.completed_at or datetime.now()

        return (
            end - self.started_at
        ).total_seconds()

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def start(self) -> None:
        """
        Marks execution as started.
        """

        self.started_at = datetime.now()
        self.completed_at = None
        self.execution_time = 0.0

        self.touch()

    def finish(
        self,
        success: bool = True,
    ) -> None:
        """
        Marks execution as completed.
        """

        self.completed_at = datetime.now()

        if self.started_at:
            self.execution_time = (
                self.completed_at
                - self.started_at
            ).total_seconds()

        self.success = success

        self.touch()

    def reset(self) -> None:
        """
        Resets runtime information.
        """

        self.started_at = None
        self.completed_at = None
        self.execution_time = 0.0
        self.success = None

        self.touch()

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __str__(self) -> str:

        if self.is_running:
            state = "Running"

        elif self.is_finished:
            state = "Finished"

        else:
            state = "Idle"

        return (
            f"{state} "
            f"({self.duration:.2f}s)"
        )