"""
Omnix V5
Workflow Model

Represents a multi-step workflow consisting of one or
more executable actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .action import Action
from .base_model import BaseModel


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(
    slots=True,
    kw_only=True,
)
class Workflow(BaseModel):
    """
    Represents an executable workflow.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    name: str

    description: str = ""

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    actions: list[Action] = field(default_factory=list)

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    status: WorkflowStatus = WorkflowStatus.IDLE

    current_step: int = 0

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------

    priority: int = 0

    stop_on_failure: bool = True

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    tags: list[str] = field(default_factory=list)

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def total_steps(self) -> int:
        return len(self.actions)

    @property
    def completed_steps(self) -> int:
        return sum(action.status.value == "completed" for action in self.actions)

    @property
    def progress(self) -> float:
        if self.total_steps == 0:
            return 0.0

        return (self.completed_steps / self.total_steps) * 100.0

    @property
    def current_action(self) -> Action | None:
        if 0 <= self.current_step < self.total_steps:
            return self.actions[self.current_step]

        return None

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def add_action(
        self,
        action: Action,
    ) -> None:
        self.actions.append(action)

    def remove_action(
        self,
        index: int,
    ) -> None:

        if 0 <= index < len(self.actions):
            self.actions.pop(index)

    def clear(self) -> None:
        self.actions.clear()
        self.current_step = 0

    def start(self) -> None:
        self.status = WorkflowStatus.RUNNING
        self.current_step = 0

    def next_step(self) -> None:

        if self.current_step < self.total_steps:
            self.current_step += 1

    def complete(self) -> None:
        self.status = WorkflowStatus.COMPLETED

    def fail(self) -> None:
        self.status = WorkflowStatus.FAILED

    def cancel(self) -> None:
        self.status = WorkflowStatus.CANCELLED

    def reset(self) -> None:
        self.status = WorkflowStatus.IDLE
        self.current_step = 0

    def __str__(self) -> str:
        return f"{self.name} " f"({self.completed_steps}/" f"{self.total_steps})"
