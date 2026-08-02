"""
Omnix V5
Action Model

Represents a single executable action that can be performed
by Omnix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base_model import BaseModel


class ActionStatus(str, Enum):
    """Current execution status of an action."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(
    slots=True,
    kw_only=True,
)
class Action(BaseModel):
    """
    Represents a single executable action.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    name: str

    action_type: str

    # ---------------------------------------------------------
    # Target
    # ---------------------------------------------------------

    target: str | None = None

    target_id: str | None = None

    # ---------------------------------------------------------
    # Parameters
    # ---------------------------------------------------------

    parameters: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    status: ActionStatus = ActionStatus.PENDING

    priority: int = 0

    timeout: float = 30.0

    retry_count: int = 0

    max_retries: int = 3

    # ---------------------------------------------------------
    # Result
    # ---------------------------------------------------------

    success: bool | None = None

    error: str | None = None

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @property
    def is_finished(self) -> bool:
        return self.status in (
            ActionStatus.COMPLETED,
            ActionStatus.FAILED,
            ActionStatus.CANCELLED,
        )

    @property
    def can_retry(self) -> bool:
        return (
            self.retry_count < self.max_retries
            and self.status == ActionStatus.FAILED
        )

    def start(self) -> None:
        self.status = ActionStatus.RUNNING

    def complete(self) -> None:
        self.status = ActionStatus.COMPLETED
        self.success = True

    def fail(self, error: str) -> None:
        self.status = ActionStatus.FAILED
        self.success = False
        self.error = error

    def cancel(self) -> None:
        self.status = ActionStatus.CANCELLED
        self.success = False

    def retry(self) -> None:
        self.retry_count += 1
        self.status = ActionStatus.PENDING
        self.error = None

    def __str__(self) -> str:
        return f"{self.name} [{self.status.value}]"