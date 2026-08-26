"""
Omnix V5 - Recovery Engine

Centralized failure recovery for the Omnix agent.

The RecoveryEngine does not execute actions itself. It analyzes a
failed step and returns a recovery decision that can be used by
GoalExecutor or AgentController.

Supported recovery actions:

    - retry
    - wait
    - alternative
    - replan
    - skip
    - stop

The engine integrates cleanly with RetryManager and WaitEngine while
remaining compatible with dictionary-based and object-based results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Dict, Optional

try:
    from .retry_manager import (
        RetryManager,
        RetryResult,
    )
except ImportError:
    from retry_manager import (
        RetryManager,
        RetryResult,
    )


# ============================================================================
# RECOVERY ACTION
# ============================================================================


class RecoveryAction(str, Enum):
    """
    Available recovery actions.
    """

    RETRY = "retry"

    WAIT = "wait"

    ALTERNATIVE = "alternative"

    REPLAN = "replan"

    SKIP = "skip"

    STOP = "stop"


# ============================================================================
# RECOVERY RESULT
# ============================================================================


@dataclass
class RecoveryResult:
    """
    Result returned by RecoveryEngine.

    action:
        The action that the executor should perform.

    success:
        True when a recovery path was found.

    retry_delay:
        Optional delay before retrying.

    alternative:
        Optional alternative action, skill or strategy.

    replan:
        True when the current workflow should be replanned.
    """

    action: RecoveryAction

    success: bool

    reason: Optional[str] = None

    error: Optional[str] = None

    retry_delay: float = 0.0

    alternative: Any = None

    replan: bool = False

    skip: bool = False

    stop: bool = False

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.action,
            RecoveryAction,
        ):

            try:

                self.action = RecoveryAction(str(self.action).strip().lower())

            except (
                TypeError,
                ValueError,
            ):

                self.action = RecoveryAction.STOP

        self.success = bool(self.success)

        try:

            self.retry_delay = float(self.retry_delay)

        except (
            TypeError,
            ValueError,
        ):

            self.retry_delay = 0.0

        self.retry_delay = max(
            0.0,
            self.retry_delay,
        )

        self.replan = bool(self.replan)

        self.skip = bool(self.skip)

        self.stop = bool(self.stop)

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

    @property
    def should_retry(
        self,
    ) -> bool:

        return self.action == RecoveryAction.RETRY

    @property
    def should_wait(
        self,
    ) -> bool:

        return self.action == RecoveryAction.WAIT

    @property
    def should_use_alternative(
        self,
    ) -> bool:

        return self.action == RecoveryAction.ALTERNATIVE

    @property
    def should_replan(
        self,
    ) -> bool:

        return self.action == RecoveryAction.REPLAN or self.replan

    @property
    def should_skip(
        self,
    ) -> bool:

        return self.action == RecoveryAction.SKIP or self.skip

    @property
    def should_stop(
        self,
    ) -> bool:

        return self.action == RecoveryAction.STOP or self.stop

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "action": (self.action.value),
            "success": self.success,
            "reason": self.reason,
            "error": self.error,
            "retry_delay": (self.retry_delay),
            "alternative": (self.alternative),
            "replan": self.replan,
            "skip": self.skip,
            "stop": self.stop,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# RECOVERY ENGINE
# ============================================================================


class RecoveryEngine:
    """
    Central recovery decision engine.

    The default recovery order is:

        1. Explicit recovery hints
        2. Alternative action if available
        3. Retry through RetryManager
        4. Replan if retry is exhausted
        5. Skip if allowed
        6. Stop

    GoalExecutor should execute the returned decision rather than
    allowing every subsystem to implement its own recovery logic.
    """

    def __init__(
        self,
        retry_manager: Optional[RetryManager] = None,
        *,
        replan_on_exhaustion: bool = True,
        allow_skip: bool = False,
    ) -> None:

        self.retry_manager = retry_manager or RetryManager()

        self.replan_on_exhaustion = bool(replan_on_exhaustion)

        self.allow_skip = bool(allow_skip)

        self._lock = RLock()

        self._recovery_count = 0
        self._retry_count = 0
        self._alternative_count = 0
        self._replan_count = 0
        self._skip_count = 0
        self._stop_count = 0

    # ====================================================================
    # MAIN RECOVERY
    # ====================================================================

    def recover(
        self,
        key: Any,
        error: Any = None,
        *,
        exception: Optional[BaseException] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Analyze a failure and return the recommended recovery action.

        Context may contain:

            alternative
            alternatives
            replan
            allow_skip
            retry
            stop
            metadata
        """

        normalized_key = self._normalize_key(key)

        context = dict(context or {})

        error_text = self._normalize_error(
            error,
            exception,
        )

        self._increment("_recovery_count")

        # ------------------------------------------------------------
        # 1. EXPLICIT STOP
        # ------------------------------------------------------------

        if context.get("stop"):

            self._increment("_stop_count")

            return self._stop_result(
                error_text,
                "Recovery was explicitly stopped.",
                context,
            )

        # ------------------------------------------------------------
        # 2. EXPLICIT REPLAN
        # ------------------------------------------------------------

        if context.get("replan"):

            self._increment("_replan_count")

            return RecoveryResult(
                action=(RecoveryAction.REPLAN),
                success=True,
                reason=("Workflow replanning was " "explicitly requested."),
                error=error_text,
                replan=True,
                metadata=self._metadata(context),
            )

        # ------------------------------------------------------------
        # 3. ALTERNATIVE ACTION
        # ------------------------------------------------------------

        alternative = self._get_alternative(context)

        if alternative is not None:

            self._increment("_alternative_count")

            return RecoveryResult(
                action=(RecoveryAction.ALTERNATIVE),
                success=True,
                reason=("An alternative recovery " "action is available."),
                error=error_text,
                alternative=alternative,
                metadata=self._metadata(context),
            )

        # ------------------------------------------------------------
        # 4. RETRY
        # ------------------------------------------------------------

        retry_allowed = context.get(
            "retry",
            True,
        )

        if retry_allowed:

            retry_result = self.retry_manager.record_failure(
                normalized_key,
                error,
                exception=exception,
                metadata=self._metadata(context),
            )

            if retry_result.should_retry:

                self._increment("_retry_count")

                return self._retry_result(
                    retry_result,
                    error_text,
                    context,
                )

        # ------------------------------------------------------------
        # 5. REPLAN AFTER RETRY EXHAUSTION
        # ------------------------------------------------------------

        replan_allowed = context.get(
            "replan_on_exhaustion",
            self.replan_on_exhaustion,
        )

        if replan_allowed:

            self._increment("_replan_count")

            return RecoveryResult(
                action=(RecoveryAction.REPLAN),
                success=True,
                reason=(
                    "Retries are unavailable or "
                    "exhausted. Workflow should "
                    "be replanned."
                ),
                error=error_text,
                replan=True,
                metadata=self._metadata(context),
            )

        # ------------------------------------------------------------
        # 6. SKIP
        # ------------------------------------------------------------

        skip_allowed = context.get(
            "allow_skip",
            self.allow_skip,
        )

        if skip_allowed:

            self._increment("_skip_count")

            return RecoveryResult(
                action=(RecoveryAction.SKIP),
                success=True,
                reason=("Failed step can be skipped."),
                error=error_text,
                skip=True,
                metadata=self._metadata(context),
            )

        # ------------------------------------------------------------
        # 7. STOP
        # ------------------------------------------------------------

        self._increment("_stop_count")

        return self._stop_result(
            error_text,
            ("No recovery strategy is " "available."),
            context,
        )

    # ====================================================================
    # SUCCESS HANDLING
    # ====================================================================

    def record_success(
        self,
        key: Any,
        *,
        clear_retry_state: bool = False,
    ) -> None:
        """
        Notify the recovery system that an operation succeeded.
        """

        self.retry_manager.record_success(
            key,
            clear=clear_retry_state,
        )

    # ====================================================================
    # MANUAL RECOVERY HELPERS
    # ====================================================================

    def retry(
        self,
        key: Any,
        error: Any = None,
        *,
        exception: Optional[BaseException] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Request retry recovery directly.
        """

        normalized_key = self._normalize_key(key)

        retry_result = self.retry_manager.record_failure(
            normalized_key,
            error,
            exception=exception,
            metadata=metadata,
        )

        error_text = self._normalize_error(
            error,
            exception,
        )

        if retry_result.should_retry:

            self._increment("_retry_count")

            return self._retry_result(
                retry_result,
                error_text,
                {"metadata": (metadata or {})},
            )

        return RecoveryResult(
            action=RecoveryAction.STOP,
            success=False,
            reason=(retry_result.reason or "Retry is unavailable."),
            error=error_text,
            stop=True,
            metadata=dict(metadata or {}),
        )

    def alternative(
        self,
        alternative: Any,
        *,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Create an alternative-action recovery result.
        """

        if alternative is None:

            return RecoveryResult(
                action=RecoveryAction.STOP,
                success=False,
                reason=("No alternative action " "was provided."),
                stop=True,
                metadata=dict(metadata or {}),
            )

        self._increment("_alternative_count")

        return RecoveryResult(
            action=(RecoveryAction.ALTERNATIVE),
            success=True,
            reason=(reason or "Alternative action selected."),
            alternative=alternative,
            metadata=dict(metadata or {}),
        )

    def request_replan(
        self,
        *,
        reason: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Explicitly request workflow replanning.
        """

        self._increment("_replan_count")

        return RecoveryResult(
            action=RecoveryAction.REPLAN,
            success=True,
            reason=(reason or "Workflow replanning requested."),
            error=error,
            replan=True,
            metadata=dict(metadata or {}),
        )

    def skip(
        self,
        *,
        reason: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Explicitly skip a recoverable step.
        """

        self._increment("_skip_count")

        return RecoveryResult(
            action=RecoveryAction.SKIP,
            success=True,
            reason=(reason or "Step skipped during recovery."),
            error=error,
            skip=True,
            metadata=dict(metadata or {}),
        )

    def stop(
        self,
        *,
        reason: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Explicitly stop recovery.
        """

        self._increment("_stop_count")

        return RecoveryResult(
            action=RecoveryAction.STOP,
            success=False,
            reason=(reason or "Recovery stopped."),
            error=error,
            stop=True,
            metadata=dict(metadata or {}),
        )

    # ====================================================================
    # INTERNAL RESULT BUILDERS
    # ====================================================================

    def _retry_result(
        self,
        retry_result: RetryResult,
        error_text: Optional[str],
        context: Dict[str, Any],
    ) -> RecoveryResult:

        delay = max(
            0.0,
            retry_result.delay,
        )

        return RecoveryResult(
            action=RecoveryAction.RETRY,
            success=True,
            reason=(retry_result.reason or "Retry permitted."),
            error=error_text,
            retry_delay=delay,
            metadata={
                **self._metadata(context),
                "retry": (retry_result.to_dict()),
            },
        )

    def _stop_result(
        self,
        error_text: Optional[str],
        reason: str,
        context: Dict[str, Any],
    ) -> RecoveryResult:

        return RecoveryResult(
            action=RecoveryAction.STOP,
            success=False,
            reason=reason,
            error=error_text,
            stop=True,
            metadata=self._metadata(context),
        )

    # ====================================================================
    # CONTEXT HELPERS
    # ====================================================================

    @staticmethod
    def _get_alternative(
        context: Dict[str, Any],
    ) -> Any:

        if context.get("alternative") is not None:

            return context.get("alternative")

        alternatives = context.get("alternatives")

        if isinstance(
            alternatives,
            (
                list,
                tuple,
            ),
        ):

            for alternative in alternatives:

                if alternative is not None:

                    return alternative

        return None

    @staticmethod
    def _metadata(
        context: Dict[str, Any],
    ) -> Dict[str, Any]:

        metadata = context.get("metadata", {})

        if not isinstance(
            metadata,
            dict,
        ):

            metadata = {"value": metadata}

        return dict(metadata)

    @staticmethod
    def _normalize_key(
        key: Any,
    ) -> str:

        if key is None:

            raise ValueError("Recovery key cannot be None.")

        key = str(key).strip()

        if not key:

            raise ValueError("Recovery key cannot be empty.")

        return key

    @staticmethod
    def _normalize_error(
        error: Any,
        exception: Optional[BaseException],
    ) -> Optional[str]:

        if exception is not None:

            return str(exception) or exception.__class__.__name__

        if error is None:

            return None

        value = str(error).strip()

        return value or None

    # ====================================================================
    # COUNTERS
    # ====================================================================

    def _increment(
        self,
        attribute: str,
    ) -> None:

        with self._lock:

            value = getattr(
                self,
                attribute,
            )

            setattr(
                self,
                attribute,
                value + 1,
            )

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return RecoveryEngine status.
        """

        with self._lock:

            return {
                "replan_on_exhaustion": (self.replan_on_exhaustion),
                "allow_skip": (self.allow_skip),
                "recovery_count": (self._recovery_count),
                "retry_count": (self._retry_count),
                "alternative_count": (self._alternative_count),
                "replan_count": (self._replan_count),
                "skip_count": (self._skip_count),
                "stop_count": (self._stop_count),
                "retry_manager": (self.retry_manager.status()),
            }


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "RecoveryAction",
    "RecoveryResult",
    "RecoveryEngine",
]
