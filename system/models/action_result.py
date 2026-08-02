"""
Omnix V5
Action Result Model

Represents the outcome of an executed action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .runtime_model import RuntimeModel


@dataclass(
    slots=True,
    kw_only=True,
)
class ActionResult(RuntimeModel):
    """
    Represents the result of executing an Action.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    action_id: str

    action_name: str

    # ---------------------------------------------------------
    # Result
    # ---------------------------------------------------------

    success: bool

    message: str = ""

    # ---------------------------------------------------------
    # Timing
    # ---------------------------------------------------------

    started_at: datetime | None = None

    completed_at: datetime | None = None

    execution_time: float = 0.0

    # ---------------------------------------------------------
    # Data
    # ---------------------------------------------------------

    data: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Error
    # ---------------------------------------------------------

    error: str | None = None

    error_type: str | None = None

    traceback: str | None = None

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    screenshot: str | None = None

    logs: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @property
    def has_error(self) -> bool:
        return self.error is not None

    @property
    def is_success(self) -> bool:
        return self.success

    def add_log(self, message: str) -> None:
        self.logs.append(message)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def set_error(
        self,
        error: str,
        error_type: str | None = None,
        traceback: str | None = None,
    ) -> None:
        self.success = False
        self.error = error
        self.error_type = error_type
        self.traceback = traceback

    def finish(self) -> None:
        """
        Marks the action as completed.
        """

        self.completed_at = datetime.now()

        if self.started_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()

    def __str__(self) -> str:

        state = "SUCCESS" if self.success else "FAILED"

        return f"{self.action_name} " f"[{state}] " f"{self.execution_time:.2f}s"
