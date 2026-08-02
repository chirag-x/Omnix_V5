"""
Omnix V5
Workflow Executor

Coordinates execution of complete automation workflows.
"""

from __future__ import annotations

import logging

from system.models.execution_result import ExecutionResult
from system.models.workflow import Workflow

from .action_executor import ActionExecutor
from .action_history import ActionHistory
from .action_queue import ActionQueue
from .execution_context import ExecutionContext
from .recovery_manager import RecoveryManager
from .retry_manager import RetryManager
from .verification import Verification

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Executes complete automation workflows.
    """

    def __init__(
        self,
        action_executor,
        verification,
        retry_manager,
        recovery_manager,
        action_history,
        action_queue,
    ):

        self._executor = action_executor

        self._verification = verification

        self._retry = retry_manager

        self._recovery = recovery_manager

        self._history = action_history

        self._queue = action_queue

        self._enabled = True

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def enabled(
        self,
    ) -> bool:

        return self._enabled

    def enable(
        self,
    ) -> None:

        self._enabled = True

    def disable(
        self,
    ) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    def execute(
        self,
        workflow: Workflow,
    ) -> ExecutionResult:

        if not self._enabled:

            return ExecutionResult(
                success=False,
                message="WorkflowExecutor disabled.",
            )

        logger.info(
            "Executing workflow: %s",
            workflow,
        )

        context = ExecutionContext(
            workflow_id=str(
                workflow.id,
            ),
            goal=getattr(
                workflow,
                "goal",
                "",
            ),
        )

        queue = ActionQueue()

        for action in workflow.actions:

            queue.enqueue(
                action,
            )

        while not self._queue.is_empty:

            action = self._queue.dequeue()

            if action is None:

                break

            try:

                result = self._retry.execute(
                    lambda a=action: self._executor.execute(
                        a,
                    )
                )

                verified = self._verification.verify(
                    action,
                    result,
                )

                self._history.record(
                    action,
                    successful=verified,
                    result=result,
                )

                if not verified:

                    raise RuntimeError("Verification failed.")

            except Exception as exc:

                context.add_error(
                    str(exc),
                )

                return self._recovery.recover(
                    action,
                    exc,
                )

        context.complete()

        return ExecutionResult(
            success=True,
            message="Workflow completed successfully.",
        )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "WorkflowExecutor(" f"enabled={self._enabled})"
