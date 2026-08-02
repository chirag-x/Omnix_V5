"""
Omnix V5
Execution Result Model

Represents the overall result of executing a workflow,
plan, or multi-step task.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .action_result import ActionResult
from .runtime_model import RuntimeModel


@dataclass(
    slots=True,
    kw_only=True,
)
class ExecutionResult(RuntimeModel):
    """
    Represents the execution result of an entire workflow.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    execution_id: str

    name: str

    # ---------------------------------------------------------
    # Overall Status
    # ---------------------------------------------------------

    success: bool = False

    cancelled: bool = False

    # ---------------------------------------------------------
    # Action Results
    # ---------------------------------------------------------

    action_results: list[ActionResult] = field(default_factory=list)

    # ---------------------------------------------------------
    # Timing
    # ---------------------------------------------------------

    started_at: datetime | None = None

    completed_at: datetime | None = None

    execution_time: float = 0.0

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    total_actions: int = 0

    completed_actions: int = 0

    failed_actions: int = 0

    skipped_actions: int = 0

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    message: str = ""

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @property
    def success_rate(self) -> float:
        """
        Returns success percentage.
        """

        if self.total_actions == 0:
            return 0.0

        return (
            self.completed_actions
            / self.total_actions
        ) * 100.0

    @property
    def has_failures(self) -> bool:
        return self.failed_actions > 0

    def add_result(
        self,
        result: ActionResult,
    ) -> None:
        """
        Adds an action result.
        """

        self.action_results.append(result)

        self.total_actions += 1

        if result.success:
            self.completed_actions += 1
        else:
            self.failed_actions += 1

    def finish(self) -> None:
        """
        Marks execution as completed.
        """

        self.completed_at = datetime.now()

        if self.started_at:
            self.execution_time = (
                self.completed_at - self.started_at
            ).total_seconds()

        self.success = (
            self.failed_actions == 0
            and not self.cancelled
        )

    def cancel(self) -> None:
        """
        Cancels execution.
        """

        self.cancelled = True
        self.success = False

    def __str__(self) -> str:

        return (
            f"{self.name} "
            f"["
            f"{self.completed_actions}/"
            f"{self.total_actions}"
            f"]"
        )