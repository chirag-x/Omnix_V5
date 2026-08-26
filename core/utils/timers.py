"""
Omnix V5 - Core Timing Utilities

Reusable timing tools for Omnix V5.

Provides:
    - High-resolution timers
    - Context-manager timing
    - Named timer registry
    - Execution duration measurement
    - Decorators for sync functions
    - Basic timer statistics

The module is intentionally lightweight and dependency-free so it can
be safely used throughout the Core and V5 subsystems.
"""

from __future__ import annotations

import functools
import threading
import time

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class TimingResult:
    """
    Result of a completed timing operation.
    """

    name: str

    started_at: float

    finished_at: float

    duration: float

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """
        Duration in milliseconds.
        """

        return self.duration * 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a serializable representation.
        """

        return {
            "name": self.name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration": self.duration,
            "duration_ms": self.duration_ms,
            "metadata": dict(self.metadata),
        }


@dataclass
class TimerStatistics:
    """
    Aggregate statistics for a named timer.
    """

    name: str

    count: int = 0

    total_duration: float = 0.0

    min_duration: Optional[float] = None

    max_duration: Optional[float] = None

    last_duration: Optional[float] = None

    @property
    def average_duration(self) -> float:
        """
        Average duration in seconds.
        """

        if self.count == 0:
            return 0.0

        return self.total_duration / self.count

    @property
    def average_duration_ms(self) -> float:
        """
        Average duration in milliseconds.
        """

        return self.average_duration * 1000.0

    @property
    def total_duration_ms(self) -> float:
        """
        Total duration in milliseconds.
        """

        return self.total_duration * 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Return serializable statistics.
        """

        return {
            "name": self.name,
            "count": self.count,
            "total_duration": (self.total_duration),
            "total_duration_ms": (self.total_duration_ms),
            "average_duration": (self.average_duration),
            "average_duration_ms": (self.average_duration_ms),
            "min_duration": (self.min_duration),
            "max_duration": (self.max_duration),
            "last_duration": (self.last_duration),
        }


# ============================================================================
# TIMER
# ============================================================================


class Timer:
    """
    High-resolution reusable timer.

    Example:

        timer = Timer("vision_analysis")

        timer.start()

        analyze_screen()

        result = timer.stop()

        print(result.duration_ms)

    The timer can also be used as a context manager:

        with Timer("startup") as timer:
            initialize_system()

        print(timer.result.duration)
    """

    def __init__(
        self,
        name: str = "timer",
        *,
        metadata: Optional[Dict[str, Any]] = None,
        auto_start: bool = False,
    ) -> None:

        self.name = self._normalize_name(name)

        self.metadata = dict(metadata or {})

        self._started_at: Optional[float] = None

        self._result: Optional[TimingResult] = None

        self._lock = threading.RLock()

        if auto_start:
            self.start()

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    def start(self) -> "Timer":
        """
        Start or restart the timer.
        """

        with self._lock:

            self._started_at = time.perf_counter()

            self._result = None

        return self

    def stop(self) -> TimingResult:
        """
        Stop the timer and return the result.
        """

        with self._lock:

            if self._started_at is None:

                raise RuntimeError(f"Timer '{self.name}' " "has not been started.")

            finished_at = time.perf_counter()

            duration = finished_at - self._started_at

            self._result = TimingResult(
                name=self.name,
                started_at=(self._started_at),
                finished_at=(finished_at),
                duration=duration,
                metadata=dict(self.metadata),
            )

            self._started_at = None

            return self._result

    def reset(self) -> None:
        """
        Reset the timer completely.
        """

        with self._lock:

            self._started_at = None

            self._result = None

    # ========================================================================
    # STATE
    # ========================================================================

    @property
    def is_running(self) -> bool:
        """
        Return True when the timer is active.
        """

        with self._lock:

            return self._started_at is not None

    @property
    def result(self) -> Optional[TimingResult]:
        """
        Return the latest completed result.
        """

        with self._lock:

            return self._result

    @property
    def elapsed(self) -> float:
        """
        Return elapsed seconds.

        Works while running or after completion.
        """

        with self._lock:

            if self._started_at is not None:

                return time.perf_counter() - self._started_at

            if self._result is not None:

                return self._result.duration

            return 0.0

    @property
    def elapsed_ms(self) -> float:
        """
        Return elapsed milliseconds.
        """

        return self.elapsed * 1000.0

    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================

    def __enter__(
        self,
    ) -> "Timer":

        self.start()

        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> bool:

        if self.is_running:
            self.stop()

        return False

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:

        if not isinstance(
            name,
            str,
        ):

            raise TypeError("Timer name must be a string.")

        name = name.strip()

        if not name:

            return "timer"

        return name

    def __repr__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"running={self.is_running}, "
            f"elapsed={self.elapsed:.6f}s"
            f")"
        )


# ============================================================================
# TIMER REGISTRY
# ============================================================================


class TimerRegistry:
    """
    Thread-safe registry for timing results and statistics.

    The registry does not keep unlimited individual history. It stores
    aggregate statistics, making it suitable for long-running Omnix
    sessions.

    Example:

        registry.record(
            TimingResult(...)
        )

        stats = registry.get(
            "skill_execution"
        )
    """

    def __init__(
        self,
    ) -> None:

        self._statistics: Dict[str, TimerStatistics] = {}

        self._lock = threading.RLock()

    def record(
        self,
        result: TimingResult,
    ) -> TimerStatistics:
        """
        Record a timing result and update statistics.
        """

        if not isinstance(
            result,
            TimingResult,
        ):

            raise TypeError("result must be a TimingResult.")

        with self._lock:

            statistics = self._statistics.get(result.name)

            if statistics is None:

                statistics = TimerStatistics(name=result.name)

                self._statistics[result.name] = statistics

            statistics.count += 1

            statistics.total_duration += result.duration

            statistics.last_duration = result.duration

            if (
                statistics.min_duration is None
                or result.duration < statistics.min_duration
            ):

                statistics.min_duration = result.duration

            if (
                statistics.max_duration is None
                or result.duration > statistics.max_duration
            ):

                statistics.max_duration = result.duration

            return TimerStatistics(
                name=statistics.name,
                count=statistics.count,
                total_duration=(statistics.total_duration),
                min_duration=(statistics.min_duration),
                max_duration=(statistics.max_duration),
                last_duration=(statistics.last_duration),
            )

    def get(
        self,
        name: str,
    ) -> Optional[TimerStatistics]:
        """
        Get statistics for a timer.
        """

        name = str(name).strip()

        with self._lock:

            statistics = self._statistics.get(name)

            if statistics is None:

                return None

            return TimerStatistics(
                name=statistics.name,
                count=statistics.count,
                total_duration=(statistics.total_duration),
                min_duration=(statistics.min_duration),
                max_duration=(statistics.max_duration),
                last_duration=(statistics.last_duration),
            )

    def all(
        self,
    ) -> Dict[str, TimerStatistics]:
        """
        Return statistics for all timers.
        """

        with self._lock:

            return {
                name: TimerStatistics(
                    name=stats.name,
                    count=stats.count,
                    total_duration=(stats.total_duration),
                    min_duration=(stats.min_duration),
                    max_duration=(stats.max_duration),
                    last_duration=(stats.last_duration),
                )
                for name, stats in self._statistics.items()
            }

    def reset(
        self,
        name: Optional[str] = None,
    ) -> None:
        """
        Reset one timer's statistics or all statistics.
        """

        with self._lock:

            if name is None:

                self._statistics.clear()

                return

            self._statistics.pop(
                str(name).strip(),
                None,
            )

    def names(
        self,
    ) -> List[str]:
        """
        Return all registered timer names.
        """

        with self._lock:

            return sorted(self._statistics.keys())

    def __len__(
        self,
    ) -> int:

        with self._lock:

            return len(self._statistics)


# ============================================================================
# GLOBAL REGISTRY
# ============================================================================


_default_registry = TimerRegistry()


def get_timer_registry() -> TimerRegistry:
    """
    Return the default Omnix timer registry.
    """

    return _default_registry


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def measure(
    name: str,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    registry: Optional[TimerRegistry] = None,
) -> Timer:
    """
    Create and automatically start a timer.

    Example:

        timer = measure(
            "vision_analysis"
        )

        analyze()

        result = timer.stop()

        registry.record(result)
    """

    timer = Timer(
        name,
        metadata=metadata,
        auto_start=True,
    )

    if registry is not None:

        original_stop = timer.stop

        def stop_and_record() -> TimingResult:

            result = original_stop()

            registry.record(result)

            return result

        timer.stop = stop_and_record  # type: ignore[method-assign]

    return timer


def time_function(
    name: Optional[str] = None,
    *,
    registry: Optional[TimerRegistry] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Callable[
    [Callable[..., T]],
    Callable[..., T],
]:
    """
    Decorator for timing synchronous functions.

    Example:

        @time_function(
            "skill_execution",
            registry=get_timer_registry(),
        )
        def execute_skill(...):
            ...
    """

    target_registry = registry or _default_registry

    def decorator(
        function: Callable[..., T],
    ) -> Callable[..., T]:

        timer_name = name or (f"{function.__module__}." f"{function.__qualname__}")

        @functools.wraps(function)
        def wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> T:

            timer = Timer(
                timer_name,
                metadata=metadata,
                auto_start=True,
            )

            try:

                return function(
                    *args,
                    **kwargs,
                )

            finally:

                result = timer.stop()

                target_registry.record(result)

        return wrapper

    return decorator


def time_call(
    callback: Callable[..., T],
    *args: Any,
    name: Optional[str] = None,
    registry: Optional[TimerRegistry] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> tuple[
    T,
    TimingResult,
]:
    """
    Execute a callable and return its result and timing information.

    Example:

        result, timing = time_call(
            process_command,
            command,
            name="command_processing",
        )
    """

    timer_name = name or (f"{callback.__module__}." f"{callback.__qualname__}")

    timer = Timer(
        timer_name,
        metadata=metadata,
        auto_start=True,
    )

    try:

        result = callback(
            *args,
            **kwargs,
        )

    finally:

        timing = timer.stop()

        (registry or _default_registry).record(timing)

    return result, timing


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "TimingResult",
    "TimerStatistics",
    "Timer",
    "TimerRegistry",
    "get_timer_registry",
    "measure",
    "time_function",
    "time_call",
]
