"""
Omnix V5
Execution Context

Shared execution state for automation workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ExecutionContext:
    """
    Shared state for an automation execution.

    This object is passed through every stage
    of workflow execution.
    """

    workflow_id: str

    goal: str = ""

    user_request: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)

    variables: dict[str, Any] = field(default_factory=dict)

    results: dict[str, Any] = field(default_factory=dict)

    errors: list[str] = field(default_factory=list)

    started_at: datetime = field(default_factory=datetime.utcnow)

    completed_at: datetime | None = None

    successful: bool = False

    cancelled: bool = False
    # ---------------------------------------------------------
    # Variables
    # ---------------------------------------------------------

    def set_variable(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.variables[key] = value

    def get_variable(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.variables.get(
            key,
            default,
        )

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    def set_result(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.results[key] = value

    def get_result(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.results.get(
            key,
            default,
        )

    # ---------------------------------------------------------
    # Errors
    # ---------------------------------------------------------

    def add_error(
        self,
        error: str,
    ) -> None:

        self.errors.append(
            error,
        )

    @property
    def has_errors(
        self,
    ) -> bool:

        return bool(
            self.errors,
        )

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def complete(
        self,
        *,
        successful: bool = True,
    ) -> None:

        self.successful = successful

        self.completed_at = datetime.utcnow()

    def cancel(
        self,
    ) -> None:

        self.cancelled = True

        self.completed_at = datetime.utcnow()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def duration(
        self,
    ) -> float | None:

        if self.completed_at is None:

            return None

        return (self.completed_at - self.started_at).total_seconds()

    def statistics(
        self,
    ) -> dict:

        return {
            "workflow_id": self.workflow_id,
            "successful": self.successful,
            "cancelled": self.cancelled,
            "has_errors": self.has_errors,
            "error_count": len(
                self.errors,
            ),
            "duration": self.duration,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return (
            "ExecutionContext("
            f"workflow_id={self.workflow_id!r}, "
            f"successful={self.successful}, "
            f"cancelled={self.cancelled})"
        )
