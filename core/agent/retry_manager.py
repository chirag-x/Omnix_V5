"""
Omnix V5 - Retry Manager

Provides controlled retry handling for workflow steps, skills,
tools and other agent operations.

The RetryManager is responsible for deciding:

    - Should this operation be retried?
    - How many retries have already happened?
    - How long should Omnix wait before retrying?
    - Is the error retryable?
    - Has the retry limit been reached?

This component does not execute retries itself.

It only manages retry policy and retry state so that components such
as GoalExecutor, RecoveryEngine and AgentController can use a single
consistent retry system.
"""

from __future__ import annotations

import time

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Dict, Iterable, Optional, Set

# ============================================================================
# RETRY DECISION
# ============================================================================


class RetryDecision(str, Enum):
    """
    Possible retry decisions.
    """

    RETRY = "retry"
    STOP = "stop"
    EXHAUSTED = "exhausted"
    NOT_RETRYABLE = "not_retryable"


# ============================================================================
# RETRY POLICY
# ============================================================================


@dataclass
class RetryPolicy:
    """
    Configuration for retry behavior.

    max_retries:
        Number of retries allowed after the initial attempt.

    initial_delay:
        Delay before the first retry.

    backoff_multiplier:
        Multiplier applied to the delay after each retry.

    max_delay:
        Maximum delay allowed.

    retryable_exceptions:
        Optional exception types that are explicitly retryable.

    non_retryable_exceptions:
        Optional exception types that should never be retried.
    """

    max_retries: int = 2

    initial_delay: float = 0.0

    backoff_multiplier: float = 2.0

    max_delay: float = 30.0

    retryable_exceptions: Optional[Iterable[type]] = None

    non_retryable_exceptions: Optional[Iterable[type]] = None

    def __post_init__(
        self,
    ) -> None:

        try:

            self.max_retries = int(self.max_retries)

        except (
            TypeError,
            ValueError,
        ):

            self.max_retries = 2

        self.max_retries = max(
            0,
            self.max_retries,
        )

        try:

            self.initial_delay = float(self.initial_delay)

        except (
            TypeError,
            ValueError,
        ):

            self.initial_delay = 0.0

        self.initial_delay = max(
            0.0,
            self.initial_delay,
        )

        try:

            self.backoff_multiplier = float(self.backoff_multiplier)

        except (
            TypeError,
            ValueError,
        ):

            self.backoff_multiplier = 2.0

        self.backoff_multiplier = max(
            1.0,
            self.backoff_multiplier,
        )

        try:

            self.max_delay = float(self.max_delay)

        except (
            TypeError,
            ValueError,
        ):

            self.max_delay = 30.0

        self.max_delay = max(
            0.0,
            self.max_delay,
        )

        if self.max_delay and self.initial_delay > self.max_delay:

            self.initial_delay = self.max_delay

        self.retryable_exceptions = self._normalize_exception_types(
            self.retryable_exceptions
        )

        self.non_retryable_exceptions = self._normalize_exception_types(
            self.non_retryable_exceptions
        )

    @staticmethod
    def _normalize_exception_types(
        values: Optional[Iterable[type]],
    ) -> Optional[Set[type]]:

        if values is None:

            return None

        normalized: Set[type] = set()

        for value in values:

            if isinstance(
                value,
                type,
            ) and issubclass(
                value,
                BaseException,
            ):

                normalized.add(value)

        return normalized

    def get_delay(
        self,
        retry_number: int,
    ) -> float:
        """
        Return the delay before a retry.

        retry_number starts at 1 for the first retry.
        """

        try:

            retry_number = int(retry_number)

        except (
            TypeError,
            ValueError,
        ):

            retry_number = 1

        retry_number = max(
            1,
            retry_number,
        )

        delay = self.initial_delay * (self.backoff_multiplier ** (retry_number - 1))

        if self.max_delay > 0:

            delay = min(
                delay,
                self.max_delay,
            )

        return max(
            0.0,
            delay,
        )

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "max_retries": (self.max_retries),
            "initial_delay": (self.initial_delay),
            "backoff_multiplier": (self.backoff_multiplier),
            "max_delay": (self.max_delay),
            "retryable_exceptions": (
                [exc.__name__ for exc in (self.retryable_exceptions or set())]
            ),
            "non_retryable_exceptions": (
                [exc.__name__ for exc in (self.non_retryable_exceptions or set())]
            ),
        }


# ============================================================================
# RETRY STATE
# ============================================================================


@dataclass
class RetryState:
    """
    Tracks retry information for one operation.
    """

    key: str

    attempts: int = 0

    retries: int = 0

    last_error: Optional[str] = None

    last_exception: Optional[BaseException] = None

    last_attempt_at: Optional[float] = None

    next_retry_at: Optional[float] = None

    exhausted: bool = False

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        self.key = str(self.key).strip()

        if not self.key:

            raise ValueError("Retry state key cannot be empty.")

        self.attempts = max(
            0,
            int(self.attempts),
        )

        self.retries = max(
            0,
            int(self.retries),
        )

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "key": self.key,
            "attempts": self.attempts,
            "retries": self.retries,
            "last_error": self.last_error,
            "last_attempt_at": (self.last_attempt_at),
            "next_retry_at": (self.next_retry_at),
            "exhausted": self.exhausted,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# RETRY RESULT
# ============================================================================


@dataclass
class RetryResult:
    """
    Result returned when evaluating a retry decision.
    """

    decision: RetryDecision

    should_retry: bool

    key: str

    attempts: int

    retries: int

    delay: float = 0.0

    reason: Optional[str] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.decision,
            RetryDecision,
        ):

            try:

                self.decision = RetryDecision(str(self.decision).strip().lower())

            except (
                TypeError,
                ValueError,
            ):

                self.decision = RetryDecision.STOP

        self.should_retry = bool(self.should_retry)

        self.key = str(self.key).strip()

        self.attempts = max(
            0,
            int(self.attempts),
        )

        self.retries = max(
            0,
            int(self.retries),
        )

        try:

            self.delay = float(self.delay)

        except (
            TypeError,
            ValueError,
        ):

            self.delay = 0.0

        self.delay = max(
            0.0,
            self.delay,
        )

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "decision": (self.decision.value),
            "should_retry": (self.should_retry),
            "key": self.key,
            "attempts": self.attempts,
            "retries": self.retries,
            "delay": self.delay,
            "reason": self.reason,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# RETRY MANAGER
# ============================================================================


class RetryManager:
    """
    Central retry policy and state manager.

    Example:

        retry_manager = RetryManager()

        result = retry_manager.record_failure(
            "step_1",
            error=error,
        )

        if result.should_retry:

            retry_manager.wait(
                result
            )

            # Execute again

    The RetryManager itself does not automatically rerun
    operations. GoalExecutor or another execution component
    remains responsible for executing the retry.
    """

    def __init__(
        self,
        policy: Optional[RetryPolicy] = None,
        *,
        max_retries: Optional[int] = None,
        initial_delay: Optional[float] = None,
        backoff_multiplier: Optional[float] = None,
        max_delay: Optional[float] = None,
    ) -> None:

        if policy is None:

            policy = RetryPolicy()

        elif not isinstance(
            policy,
            RetryPolicy,
        ):

            if isinstance(
                policy,
                dict,
            ):

                policy = RetryPolicy(**policy)

            else:

                raise TypeError("policy must be a RetryPolicy " "or dictionary.")

        if max_retries is not None:

            policy.max_retries = max(
                0,
                int(max_retries),
            )

        if initial_delay is not None:

            policy.initial_delay = max(
                0.0,
                float(initial_delay),
            )

        if backoff_multiplier is not None:

            policy.backoff_multiplier = max(
                1.0,
                float(backoff_multiplier),
            )

        if max_delay is not None:

            policy.max_delay = max(
                0.0,
                float(max_delay),
            )

        self.policy = policy

        self._states: Dict[str, RetryState] = {}

        self._lock = RLock()

        self._total_attempts = 0
        self._total_retries = 0
        self._total_exhausted = 0

    # ====================================================================
    # MAIN FAILURE HANDLING
    # ====================================================================

    def record_failure(
        self,
        key: Any,
        error: Any = None,
        *,
        exception: Optional[BaseException] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RetryResult:
        """
        Record a failed operation and determine whether it should retry.

        This should be called after an execution attempt fails.
        """

        normalized_key = self._normalize_key(key)

        if exception is None and isinstance(
            error,
            BaseException,
        ):

            exception = error

        error_text = self._normalize_error(
            error,
            exception,
        )

        with self._lock:

            state = self._get_or_create_state(normalized_key)

            state.attempts += 1

            state.last_attempt_at = time.time()

            state.last_error = error_text

            state.last_exception = exception

            if metadata:

                state.metadata.update(dict(metadata))

            self._total_attempts += 1

            retryability = self._is_retryable_exception(exception)

            if retryability is False:

                state.exhausted = True
                state.next_retry_at = None

                return RetryResult(
                    decision=(RetryDecision.NOT_RETRYABLE),
                    should_retry=False,
                    key=normalized_key,
                    attempts=state.attempts,
                    retries=state.retries,
                    reason=("The failure is marked as " "non-retryable."),
                    error=error_text,
                    metadata=dict(state.metadata),
                )

            if state.retries >= self.policy.max_retries:

                if not state.exhausted:

                    self._total_exhausted += 1

                state.exhausted = True
                state.next_retry_at = None

                return RetryResult(
                    decision=(RetryDecision.EXHAUSTED),
                    should_retry=False,
                    key=normalized_key,
                    attempts=state.attempts,
                    retries=state.retries,
                    reason=("Maximum retry limit reached."),
                    error=error_text,
                    metadata=dict(state.metadata),
                )

            state.retries += 1

            self._total_retries += 1

            delay = self.policy.get_delay(state.retries)

            state.next_retry_at = time.time() + delay

            return RetryResult(
                decision=RetryDecision.RETRY,
                should_retry=True,
                key=normalized_key,
                attempts=state.attempts,
                retries=state.retries,
                delay=delay,
                reason=("Retry permitted by the " "current retry policy."),
                error=error_text,
                metadata=dict(state.metadata),
            )

    def record_success(
        self,
        key: Any,
        *,
        clear: bool = False,
    ) -> Optional[RetryState]:
        """
        Record successful completion.

        By default, retry history is preserved for debugging.
        Use clear=True to remove the state completely.
        """

        normalized_key = self._normalize_key(key)

        with self._lock:

            state = self._states.get(normalized_key)

            if state is None:

                return None

            state.exhausted = False
            state.next_retry_at = None
            state.last_error = None
            state.last_exception = None

            if clear:

                del self._states[normalized_key]

                return None

            return state

    def record_attempt(
        self,
        key: Any,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RetryState:
        """
        Record an attempt when execution begins.

        This is optional. record_failure() also records an attempt.
        Use this when you want attempt tracking before execution.
        """

        normalized_key = self._normalize_key(key)

        with self._lock:

            state = self._get_or_create_state(normalized_key)

            state.attempts += 1

            state.last_attempt_at = time.time()

            if metadata:

                state.metadata.update(dict(metadata))

            self._total_attempts += 1

            return state

    # ====================================================================
    # RETRY DECISION HELPERS
    # ====================================================================

    def should_retry(
        self,
        key: Any,
    ) -> bool:
        """
        Check whether the operation can still retry.
        """

        normalized_key = self._normalize_key(key)

        with self._lock:

            state = self._states.get(normalized_key)

            if state is None:

                return self.policy.max_retries > 0

            if state.exhausted:

                return False

            return state.retries < self.policy.max_retries

    def get_delay(
        self,
        key: Any,
    ) -> float:
        """
        Return remaining delay before the next retry.
        """

        normalized_key = self._normalize_key(key)

        with self._lock:

            state = self._states.get(normalized_key)

            if state is None or state.next_retry_at is None:

                return 0.0

            remaining = state.next_retry_at - time.time()

            return max(
                0.0,
                remaining,
            )

    def can_retry_now(
        self,
        key: Any,
    ) -> bool:
        """
        Return True when retry is allowed immediately.
        """

        return self.should_retry(key) and self.get_delay(key) <= 0.0

    def wait(
        self,
        retry: Any,
    ) -> float:
        """
        Wait for a retry delay.

        Accepts RetryResult or an operation key.

        Returns the actual wait duration.
        """

        if isinstance(
            retry,
            RetryResult,
        ):

            delay = retry.delay

        else:

            delay = self.get_delay(retry)

        delay = max(
            0.0,
            float(delay),
        )

        if delay > 0:

            time.sleep(delay)

        return delay

    # ====================================================================
    # EXCEPTION POLICY
    # ====================================================================

    def is_retryable(
        self,
        error: Any = None,
        *,
        exception: Optional[BaseException] = None,
    ) -> bool:
        """
        Public helper for checking retryability.
        """

        if exception is None and isinstance(
            error,
            BaseException,
        ):

            exception = error

        result = self._is_retryable_exception(exception)

        if result is None:

            return True

        return result

    def _is_retryable_exception(
        self,
        exception: Optional[BaseException],
    ) -> Optional[bool]:

        if exception is None:

            return None

        non_retryable = self.policy.non_retryable_exceptions

        if non_retryable:

            if isinstance(
                exception,
                tuple(non_retryable),
            ):

                return False

        retryable = self.policy.retryable_exceptions

        if retryable:

            if isinstance(
                exception,
                tuple(retryable),
            ):

                return True

            return False

        return None

    # ====================================================================
    # STATE MANAGEMENT
    # ====================================================================

    def get_state(
        self,
        key: Any,
    ) -> Optional[RetryState]:
        """
        Return retry state for an operation.
        """

        normalized_key = self._normalize_key(key)

        with self._lock:

            return self._states.get(normalized_key)

    def reset(
        self,
        key: Any,
    ) -> bool:
        """
        Reset retry history for one operation.
        """

        normalized_key = self._normalize_key(key)

        with self._lock:

            if normalized_key not in self._states:

                return False

            del self._states[normalized_key]

            return True

    def clear(
        self,
    ) -> None:
        """
        Remove all retry states.
        """

        with self._lock:

            self._states.clear()

    def get_states(
        self,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Return serializable retry state information.
        """

        with self._lock:

            return {key: state.to_dict() for key, state in self._states.items()}

    # ====================================================================
    # POLICY MANAGEMENT
    # ====================================================================

    def set_policy(
        self,
        policy: RetryPolicy,
    ) -> None:
        """
        Replace the current retry policy.
        """

        if not isinstance(
            policy,
            RetryPolicy,
        ):

            if isinstance(
                policy,
                dict,
            ):

                policy = RetryPolicy(**policy)

            else:

                raise TypeError("policy must be a RetryPolicy " "or dictionary.")

        with self._lock:

            self.policy = policy

    # ====================================================================
    # INTERNAL UTILITIES
    # ====================================================================

    def _get_or_create_state(
        self,
        key: str,
    ) -> RetryState:

        state = self._states.get(key)

        if state is None:

            state = RetryState(key=key)

            self._states[key] = state

        return state

    @staticmethod
    def _normalize_key(
        key: Any,
    ) -> str:

        if key is None:

            raise ValueError("Retry key cannot be None.")

        normalized = str(key).strip()

        if not normalized:

            raise ValueError("Retry key cannot be empty.")

        return normalized

    @staticmethod
    def _normalize_error(
        error: Any,
        exception: Optional[BaseException],
    ) -> Optional[str]:

        if exception is not None:

            return str(exception) or exception.__class__.__name__

        if error is None:

            return None

        text = str(error).strip()

        return text or None

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return RetryManager status.
        """

        with self._lock:

            active_states = len(self._states)

            exhausted_states = sum(
                1 for state in self._states.values() if state.exhausted
            )

            return {
                "active_states": (active_states),
                "exhausted_states": (exhausted_states),
                "total_attempts": (self._total_attempts),
                "total_retries": (self._total_retries),
                "total_exhausted": (self._total_exhausted),
                "policy": (self.policy.to_dict()),
            }


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "RetryDecision",
    "RetryPolicy",
    "RetryState",
    "RetryResult",
    "RetryManager",
]
