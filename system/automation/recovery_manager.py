"""
Omnix V5
Recovery Manager

Handles recovery after automation failures.
"""

from __future__ import annotations

import logging

from system.models.action import Action
from system.models.execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class RecoveryManager:
    """
    Performs recovery after failed automation.

    Recovery may include cleanup, rollback,
    or restoring a safe execution state.
    """

    def __init__(self) -> None:

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
    # Recovery
    # ---------------------------------------------------------

    def recover(
        self,
        action: Action,
        exception: Exception,
    ) -> ExecutionResult:

        if not self._enabled:

            return ExecutionResult(
                success=False,
                message="Recovery disabled.",
            )

        logger.error(
            "Recovering from failed action %s: %s",
            action,
            exception,
        )

        return ExecutionResult(
            success=False,
            message=str(
                exception,
            ),
        )

    def rollback(
        self,
        action: Action,
    ) -> bool:

        if not self._enabled:

            return False

        logger.info(
            "Rollback requested for %s",
            action,
        )

        #
        # Future rollback implementation
        #

        return False

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

        return "RecoveryManager(" f"enabled={self._enabled})"
