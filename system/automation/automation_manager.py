"""
Omnix V5
Automation Manager

Public API for the automation subsystem.
"""

from __future__ import annotations

import logging

from .action_executor import ActionExecutor
from .action_history import ActionHistory
from .action_queue import ActionQueue
from .recovery_manager import RecoveryManager
from .retry_manager import RetryManager
from .safety_manager import SafetyManager
from .verification import Verification
from .workflow_executor import WorkflowExecutor

from system.models.action import Action
from system.models.action_result import ActionResult
from system.models.execution_result import ExecutionResult
from system.models.workflow import Workflow

logger = logging.getLogger(__name__)


class AutomationManager:
    """
    Public interface for the automation subsystem.

    Coordinates all automation services and exposes
    a simple API for workflow execution.
    """

    def __init__(
        self,
        action_executor: ActionExecutor,
    ) -> None:

        #
        # Core Services
        #

        self._queue = ActionQueue()

        self._history = ActionHistory()

        self._verification = Verification()

        self._retry = RetryManager()

        self._recovery = RecoveryManager()

        self._safety = SafetyManager()

        self._executor = action_executor

        self._workflow_executor = WorkflowExecutor(
            action_executor=self._executor,
            verification=self._verification,
            retry_manager=self._retry,
            recovery_manager=self._recovery,
            action_history=self._history,
            action_queue=self._queue,
        )

        self._initialized = False

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    @property
    def initialized(
        self,
    ) -> bool:

        return self._initialized

    def initialize(
        self,
    ) -> None:

        if self._initialized:

            return

        logger.info("Initializing AutomationManager...")

        self._initialized = True

        logger.info("AutomationManager initialized.")

    def shutdown(
        self,
    ) -> None:

        if not self._initialized:

            return

        logger.info("Shutting down AutomationManager...")

        self._queue.clear()

        self._initialized = False

    # ---------------------------------------------------------
    # Services
    # ---------------------------------------------------------

    @property
    def queue(
        self,
    ) -> ActionQueue:

        return self._queue

    @property
    def history(
        self,
    ) -> ActionHistory:

        return self._history

    @property
    def verification(
        self,
    ) -> Verification:

        return self._verification

    @property
    def retry_manager(
        self,
    ) -> RetryManager:

        return self._retry

    @property
    def recovery_manager(
        self,
    ) -> RecoveryManager:

        return self._recovery

    @property
    def safety_manager(
        self,
    ) -> SafetyManager:

        return self._safety

    @property
    def action_executor(
        self,
    ) -> ActionExecutor:

        return self._executor

    @property
    def workflow_executor(
        self,
    ) -> WorkflowExecutor:

        return self._workflow_executor

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    def execute_workflow(
        self,
        workflow: Workflow,
    ) -> ExecutionResult:

        if not self._initialized:

            raise RuntimeError("AutomationManager is not initialized.")

        logger.info("Executing workflow...")

        return self._workflow_executor.execute(
            workflow,
        )

    def execute_action(
        self,
        action: Action,
    ) -> ActionResult:

        if not self._initialized:

            raise RuntimeError("AutomationManager is not initialized.")

        if not self._safety.validate(
            action,
        ):

            logger.warning(
                "SafetyManager blocked action: %s",
                action,
            )

            return ActionResult(
                success=False,
                message="Action blocked by SafetyManager.",
            )

        return self._executor.execute(
            action,
        )

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def clear_history(
        self,
    ) -> None:

        self._history.clear()

    def clear_queue(
        self,
    ) -> None:

        self._queue.clear()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "initialized": self._initialized,
            "queue": self._queue.statistics(),
            "history": self._history.statistics(),
            "verification": self._verification.statistics(),
            "retry": self._retry.statistics(),
            "recovery": self._recovery.statistics(),
            "safety": self._safety.statistics(),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "AutomationManager(" f"initialized={self._initialized})"
