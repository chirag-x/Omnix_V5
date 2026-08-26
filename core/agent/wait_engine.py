"""
Omnix V5 - Wait Engine

Provides controlled waiting and condition polling for the Omnix agent.

The WaitEngine can:

    - Wait for a fixed duration
    - Wait until a condition becomes true
    - Poll conditions at configurable intervals
    - Enforce timeouts
    - Support cancellation
    - Return normalized wait results

The WaitEngine does not own workflow execution. It is used by
GoalExecutor, RecoveryEngine, RetryManager integrations and other
components that need controlled waiting.
"""

from __future__ import annotations

import inspect
import time

from dataclasses import dataclass, field
from enum import Enum
from threading import Event, RLock
from typing import Any, Callable, Dict, Optional

# ============================================================================
# WAIT STATUS
# ============================================================================


class WaitStatus(str, Enum):
    """
    Possible wait outcomes.
    """

    COMPLETED = "completed"
    CONDITION_MET = "condition_met"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    FAILED = "failed"


# ============================================================================
# WAIT RESULT
# ============================================================================


@dataclass
class WaitResult:
    """
    Normalized result returned by WaitEngine.
    """

    status: WaitStatus

    success: bool

    elapsed: float = 0.0

    timeout: Optional[float] = None

    polls: int = 0

    value: Any = None

    reason: Optional[str] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.status,
            WaitStatus,
        ):

            try:

                self.status = WaitStatus(str(self.status).strip().lower())

            except (
                TypeError,
                ValueError,
            ):

                self.status = WaitStatus.FAILED

        self.success = bool(self.success)

        try:

            self.elapsed = float(self.elapsed)

        except (
            TypeError,
            ValueError,
        ):

            self.elapsed = 0.0

        self.elapsed = max(
            0.0,
            self.elapsed,
        )

        if self.timeout is not None:

            try:

                self.timeout = float(self.timeout)

            except (
                TypeError,
                ValueError,
            ):

                self.timeout = None

            if self.timeout is not None:

                self.timeout = max(
                    0.0,
                    self.timeout,
                )

        try:

            self.polls = int(self.polls)

        except (
            TypeError,
            ValueError,
        ):

            self.polls = 0

        self.polls = max(
            0,
            self.polls,
        )

        if self.reason is not None:

            self.reason = str(self.reason).strip() or None

        if self.error is not None:

            self.error = str(self.error).strip() or None

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

    @property
    def timed_out(
        self,
    ) -> bool:

        return self.status == WaitStatus.TIMEOUT

    @property
    def cancelled(
        self,
    ) -> bool:

        return self.status == WaitStatus.CANCELLED

    @property
    def failed(
        self,
    ) -> bool:

        return self.status == WaitStatus.FAILED

    @property
    def condition_met(
        self,
    ) -> bool:

        return self.status == WaitStatus.CONDITION_MET

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "status": self.status.value,
            "success": self.success,
            "elapsed": self.elapsed,
            "timeout": self.timeout,
            "polls": self.polls,
            "value": self.value,
            "reason": self.reason,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# WAIT ENGINE
# ============================================================================


class WaitEngine:
    """
    Central waiting and condition polling engine.

    The engine supports both simple waits and condition-based waits.

    Example:

        wait_engine = WaitEngine()

        result = wait_engine.wait(
            2.0
        )

        result = wait_engine.wait_for(
            lambda: application_is_ready(),
            timeout=10.0,
            interval=0.5,
        )

    Cancellation can be controlled with threading.Event:

        cancel_event = Event()

        result = wait_engine.wait_for(
            condition,
            timeout=30,
            cancel_event=cancel_event,
        )
    """

    def __init__(
        self,
        *,
        default_interval: float = 0.25,
        max_interval: float = 5.0,
        sleep_function: Callable[
            [float],
            None,
        ] = time.sleep,
        clock: Callable[
            [],
            float,
        ] = time.monotonic,
    ) -> None:

        self.default_interval = self._normalize_interval(
            default_interval,
            default=0.25,
        )

        self.max_interval = self._normalize_interval(
            max_interval,
            default=5.0,
        )

        if self.default_interval > self.max_interval:

            self.default_interval = self.max_interval

        if not callable(sleep_function):

            raise TypeError("sleep_function must be callable.")

        if not callable(clock):

            raise TypeError("clock must be callable.")

        self._sleep = sleep_function
        self._clock = clock

        self._lock = RLock()

        self._wait_count = 0
        self._completed_count = 0
        self._timeout_count = 0
        self._cancelled_count = 0
        self._failed_count = 0

    # ====================================================================
    # SIMPLE WAIT
    # ====================================================================

    def wait(
        self,
        duration: Any,
        *,
        cancel_event: Optional[Event] = None,
        check_interval: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WaitResult:
        """
        Wait for a fixed duration.

        If a cancellation event is supplied, the wait is split into
        intervals so cancellation can be detected.
        """

        try:

            duration = float(duration)

        except (
            TypeError,
            ValueError,
        ):

            return self._failure_result(
                error=("Invalid wait duration."),
                metadata=metadata,
            )

        if duration < 0:

            return self._failure_result(
                error=("Wait duration cannot be negative."),
                metadata=metadata,
            )

        interval = self._resolve_interval(check_interval)

        started_at = self._clock()

        self._increment("_wait_count")

        if cancel_event is not None and cancel_event.is_set():

            self._increment("_cancelled_count")

            return WaitResult(
                status=WaitStatus.CANCELLED,
                success=False,
                elapsed=0.0,
                reason=("Wait was cancelled before " "execution."),
                metadata=dict(metadata or {}),
            )

        if duration == 0:

            self._increment("_completed_count")

            return WaitResult(
                status=WaitStatus.COMPLETED,
                success=True,
                elapsed=0.0,
                reason=("Wait completed immediately."),
                metadata=dict(metadata or {}),
            )

        deadline = started_at + duration

        while True:

            if cancel_event is not None and cancel_event.is_set():

                elapsed = self._clock() - started_at

                self._increment("_cancelled_count")

                return WaitResult(
                    status=WaitStatus.CANCELLED,
                    success=False,
                    elapsed=elapsed,
                    reason=("Wait was cancelled."),
                    metadata=dict(metadata or {}),
                )

            remaining = deadline - self._clock()

            if remaining <= 0:

                elapsed = self._clock() - started_at

                self._increment("_completed_count")

                return WaitResult(
                    status=WaitStatus.COMPLETED,
                    success=True,
                    elapsed=elapsed,
                    timeout=duration,
                    reason=("Wait completed successfully."),
                    metadata=dict(metadata or {}),
                )

            sleep_time = min(
                interval,
                remaining,
            )

            self._sleep(sleep_time)

    # ====================================================================
    # CONDITION WAITING
    # ====================================================================

    def wait_for(
        self,
        condition: Callable[
            ...,
            Any,
        ],
        *,
        timeout: Optional[float] = None,
        interval: Optional[float] = None,
        cancel_event: Optional[Event] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        raise_condition_errors: bool = False,
    ) -> WaitResult:
        """
        Wait until a condition evaluates as successful.

        The condition may return:

            True / False
            Any truthy/falsy value
            Dictionary containing "success"
            Object containing "success"

        The original condition result is returned as WaitResult.value.
        """

        if not callable(condition):

            return self._failure_result(
                error=("Condition must be callable."),
                metadata=metadata,
            )

        normalized_timeout = self._normalize_timeout(timeout)

        if timeout is not None and normalized_timeout is None:

            return self._failure_result(
                error=("Invalid timeout value."),
                metadata=metadata,
            )

        poll_interval = self._resolve_interval(interval)

        started_at = self._clock()

        deadline = None

        if normalized_timeout is not None:

            deadline = started_at + normalized_timeout

        polls = 0

        self._increment("_wait_count")

        while True:

            if cancel_event is not None and cancel_event.is_set():

                elapsed = self._clock() - started_at

                self._increment("_cancelled_count")

                return WaitResult(
                    status=WaitStatus.CANCELLED,
                    success=False,
                    elapsed=elapsed,
                    timeout=normalized_timeout,
                    polls=polls,
                    reason=("Condition wait was cancelled."),
                    metadata=dict(metadata or {}),
                )

            if deadline is not None and self._clock() >= deadline:

                elapsed = self._clock() - started_at

                self._increment("_timeout_count")

                return WaitResult(
                    status=WaitStatus.TIMEOUT,
                    success=False,
                    elapsed=elapsed,
                    timeout=normalized_timeout,
                    polls=polls,
                    reason=("Condition was not met " "before timeout."),
                    metadata=dict(metadata or {}),
                )

            try:

                value = self._evaluate_condition(
                    condition,
                    context=context,
                )

                polls += 1

                if self._is_condition_success(value):

                    elapsed = self._clock() - started_at

                    self._increment("_completed_count")

                    return WaitResult(
                        status=(WaitStatus.CONDITION_MET),
                        success=True,
                        elapsed=elapsed,
                        timeout=normalized_timeout,
                        polls=polls,
                        value=value,
                        reason=("Condition was met."),
                        metadata=dict(metadata or {}),
                    )

            except Exception as error:

                if raise_condition_errors:

                    raise

                elapsed = self._clock() - started_at

                self._increment("_failed_count")

                return WaitResult(
                    status=WaitStatus.FAILED,
                    success=False,
                    elapsed=elapsed,
                    timeout=normalized_timeout,
                    polls=polls,
                    reason=("Condition evaluation failed."),
                    error=str(error),
                    metadata=dict(metadata or {}),
                )

            if deadline is None:

                sleep_time = poll_interval

            else:

                remaining = deadline - self._clock()

                if remaining <= 0:

                    continue

                sleep_time = min(
                    poll_interval,
                    remaining,
                )

            self._sleep(sleep_time)

    # ====================================================================
    # WAIT UNTIL ALREADY-KNOWN TIME
    # ====================================================================

    def wait_until(
        self,
        target_time: float,
        *,
        cancel_event: Optional[Event] = None,
        interval: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WaitResult:
        """
        Wait until a target monotonic clock time.

        target_time must use the same time source as the engine clock.
        """

        try:

            target_time = float(target_time)

        except (
            TypeError,
            ValueError,
        ):

            return self._failure_result(
                error=("Invalid target time."),
                metadata=metadata,
            )

        remaining = target_time - self._clock()

        return self.wait(
            max(
                0.0,
                remaining,
            ),
            cancel_event=cancel_event,
            check_interval=interval,
            metadata=metadata,
        )

    # ====================================================================
    # CONDITION UTILITIES
    # ====================================================================

    @staticmethod
    def _evaluate_condition(
        condition: Callable[
            ...,
            Any,
        ],
        *,
        context: Optional[Dict[str, Any]],
    ) -> Any:
        """
        Invoke a condition while supporting simple callables and
        callables that accept context.
        """

        context = dict(context or {})

        try:

            signature = inspect.signature(condition)

            parameters = signature.parameters

            accepts_kwargs = any(
                parameter.kind == parameter.VAR_KEYWORD
                for parameter in parameters.values()
            )

            if accepts_kwargs:

                return condition(**context)

            if not parameters:

                return condition()

            if "context" in parameters:

                return condition(context=context)

            filtered = {
                name: value for name, value in context.items() if name in parameters
            }

            if filtered:

                return condition(**filtered)

            return condition()

        except (
            TypeError,
            ValueError,
        ):

            return condition()

    @staticmethod
    def _is_condition_success(
        value: Any,
    ) -> bool:
        """
        Normalize condition results.
        """

        if isinstance(
            value,
            bool,
        ):

            return value

        if isinstance(
            value,
            dict,
        ):

            if "success" in value:

                return bool(value["success"])

            if "ok" in value:

                return bool(value["ok"])

            if "ready" in value:

                return bool(value["ready"])

            if "completed" in value:

                return bool(value["completed"])

            return bool(value)

        if hasattr(
            value,
            "success",
        ):

            try:

                return bool(value.success)

            except Exception:

                pass

        if hasattr(
            value,
            "ok",
        ):

            try:

                return bool(value.ok)

            except Exception:

                pass

        return bool(value)

    # ====================================================================
    # CONFIGURATION
    # ====================================================================

    def set_default_interval(
        self,
        interval: Any,
    ) -> None:
        """
        Update the default polling interval.
        """

        normalized = self._normalize_interval(
            interval,
            default=self.default_interval,
        )

        with self._lock:

            self.default_interval = min(
                normalized,
                self.max_interval,
            )

    def set_max_interval(
        self,
        interval: Any,
    ) -> None:
        """
        Update the maximum allowed interval.
        """

        normalized = self._normalize_interval(
            interval,
            default=self.max_interval,
        )

        with self._lock:

            self.max_interval = normalized

            if self.default_interval > self.max_interval:

                self.default_interval = self.max_interval

    # ====================================================================
    # INTERNAL HELPERS
    # ====================================================================

    def _resolve_interval(
        self,
        interval: Optional[float],
    ) -> float:

        if interval is None:

            with self._lock:

                return self.default_interval

        normalized = self._normalize_interval(
            interval,
            default=self.default_interval,
        )

        with self._lock:

            return min(
                normalized,
                self.max_interval,
            )

    @staticmethod
    def _normalize_interval(
        value: Any,
        *,
        default: float,
    ) -> float:

        try:

            interval = float(value)

        except (
            TypeError,
            ValueError,
        ):

            interval = default

        return max(
            0.001,
            interval,
        )

    @staticmethod
    def _normalize_timeout(
        timeout: Optional[float],
    ) -> Optional[float]:

        if timeout is None:

            return None

        try:

            value = float(timeout)

        except (
            TypeError,
            ValueError,
        ):

            return None

        return max(
            0.0,
            value,
        )

    def _failure_result(
        self,
        *,
        error: str,
        metadata: Optional[Dict[str, Any]],
    ) -> WaitResult:

        self._increment("_wait_count")

        self._increment("_failed_count")

        return WaitResult(
            status=WaitStatus.FAILED,
            success=False,
            error=error,
            metadata=dict(metadata or {}),
        )

    def _increment(
        self,
        attribute: str,
    ) -> None:

        with self._lock:

            current = getattr(
                self,
                attribute,
            )

            setattr(
                self,
                attribute,
                current + 1,
            )

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return WaitEngine status and counters.
        """

        with self._lock:

            return {
                "default_interval": (self.default_interval),
                "max_interval": (self.max_interval),
                "wait_count": (self._wait_count),
                "completed_count": (self._completed_count),
                "timeout_count": (self._timeout_count),
                "cancelled_count": (self._cancelled_count),
                "failed_count": (self._failed_count),
            }


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "WaitStatus",
    "WaitResult",
    "WaitEngine",
]
