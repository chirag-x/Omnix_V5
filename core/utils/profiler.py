"""
Omnix V5 - Core Profiling Utilities

Lightweight profiling tools for Omnix V5.

Provides:
    - Named profiling sessions
    - Nested execution sections
    - Section statistics
    - Context-manager profiling
    - Function decorators
    - Thread-safe profile storage

This module complements timers.py:

    timers.py
        Measures individual operations.

    profiler.py
        Tracks multiple named sections inside a larger operation.

Example:

    with Profiler("command_execution") as profiler:
        with profiler.section("intent"):
            detect_intent()

        with profiler.section("planning"):
            create_plan()

        with profiler.section("execution"):
            execute_plan()
"""

from __future__ import annotations

import functools
import threading
import time

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ProfileEntry:
    """
    Represents one completed profiling section.
    """

    name: str

    started_at: float

    finished_at: float

    duration: float

    depth: int = 0

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """
        Duration in milliseconds.
        """

        return self.duration * 1000.0

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable representation.
        """

        return {
            "name": self.name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration": self.duration,
            "duration_ms": self.duration_ms,
            "depth": self.depth,
            "metadata": dict(self.metadata),
        }


@dataclass
class ProfileStatistics:
    """
    Aggregate statistics for a profiling section.
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
    def total_duration_ms(self) -> float:
        """
        Total duration in milliseconds.
        """

        return self.total_duration * 1000.0

    @property
    def average_duration_ms(self) -> float:
        """
        Average duration in milliseconds.
        """

        return self.average_duration * 1000.0

    @property
    def min_duration_ms(
        self,
    ) -> Optional[float]:

        if self.min_duration is None:

            return None

        return self.min_duration * 1000.0

    @property
    def max_duration_ms(
        self,
    ) -> Optional[float]:

        if self.max_duration is None:

            return None

        return self.max_duration * 1000.0

    @property
    def last_duration_ms(
        self,
    ) -> Optional[float]:

        if self.last_duration is None:

            return None

        return self.last_duration * 1000.0

    def record(
        self,
        duration: float,
    ) -> None:
        """
        Update statistics with a new duration.
        """

        duration = float(duration)

        self.count += 1

        self.total_duration += duration

        self.last_duration = duration

        if self.min_duration is None or duration < self.min_duration:

            self.min_duration = duration

        if self.max_duration is None or duration > self.max_duration:

            self.max_duration = duration

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return serializable statistics.
        """

        return {
            "name": self.name,
            "count": self.count,
            "total_duration": self.total_duration,
            "total_duration_ms": (self.total_duration_ms),
            "average_duration": (self.average_duration),
            "average_duration_ms": (self.average_duration_ms),
            "min_duration": self.min_duration,
            "min_duration_ms": (self.min_duration_ms),
            "max_duration": self.max_duration,
            "max_duration_ms": (self.max_duration_ms),
            "last_duration": self.last_duration,
            "last_duration_ms": (self.last_duration_ms),
        }


@dataclass
class ProfileResult:
    """
    Final result of a profiling session.
    """

    name: str

    started_at: float

    finished_at: float

    duration: float

    entries: List[ProfileEntry] = field(default_factory=list)

    statistics: Dict[str, ProfileStatistics] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """
        Total profile duration in milliseconds.
        """

        return self.duration * 1000.0

    def to_dict(
        self,
        *,
        include_entries: bool = True,
    ) -> Dict[str, Any]:
        """
        Return a serializable profile result.
        """

        data = {
            "name": self.name,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration": self.duration,
            "duration_ms": self.duration_ms,
            "statistics": {
                name: stats.to_dict() for name, stats in self.statistics.items()
            },
            "metadata": dict(self.metadata),
        }

        if include_entries:

            data["entries"] = [entry.to_dict() for entry in self.entries]

        return data


# ============================================================================
# PROFILE SECTION
# ============================================================================


class ProfileSection:
    """
    Context manager representing a section inside a Profiler.
    """

    def __init__(
        self,
        profiler: "Profiler",
        name: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:

        self._profiler = profiler

        self.name = name

        self.metadata = dict(metadata or {})

        self._started_at: Optional[float] = None

        self._depth = 0

        self._completed = False

    def __enter__(
        self,
    ) -> "ProfileSection":

        self._started_at = time.perf_counter()

        self._depth = self._profiler._enter_section(self.name)

        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> bool:

        try:

            if self._started_at is not None and not self._completed:

                finished_at = time.perf_counter()

                duration = finished_at - self._started_at

                self._profiler._record_section(
                    name=self.name,
                    started_at=(self._started_at),
                    finished_at=finished_at,
                    duration=duration,
                    depth=self._depth,
                    metadata=self.metadata,
                )

                self._completed = True

        finally:

            self._profiler._exit_section()

        return False


# ============================================================================
# PROFILER
# ============================================================================


class Profiler:
    """
    Thread-safe lightweight profiler.

    Example:

        with Profiler("omnix_startup") as profiler:

            with profiler.section(
                "services"
            ):
                initialize_services()

            with profiler.section(
                "vision"
            ):
                initialize_vision()

        result = profiler.result
    """

    def __init__(
        self,
        name: str = "profile",
        *,
        metadata: Optional[Dict[str, Any]] = None,
        max_entries: int = 10000,
    ) -> None:

        if max_entries < 1:

            raise ValueError("max_entries must be " "at least 1.")

        self.name = self._normalize_name(name)

        self.metadata = dict(metadata or {})

        self._max_entries = max_entries

        self._started_at: Optional[float] = None

        self._result: Optional[ProfileResult] = None

        self._entries: List[ProfileEntry] = []

        self._statistics: Dict[str, ProfileStatistics] = {}

        self._local = threading.local()

        self._lock = threading.RLock()

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    def start(
        self,
    ) -> "Profiler":
        """
        Start or restart the profiling session.
        """

        with self._lock:

            self._started_at = time.perf_counter()

            self._result = None

            self._entries.clear()

            self._statistics.clear()

        self._set_depth(0)

        return self

    def stop(
        self,
    ) -> ProfileResult:
        """
        Stop profiling and return the result.
        """

        with self._lock:

            if self._started_at is None:

                raise RuntimeError(f"Profiler '{self.name}' " "has not been started.")

            finished_at = time.perf_counter()

            duration = finished_at - self._started_at

            statistics_copy = {
                name: ProfileStatistics(
                    name=stats.name,
                    count=stats.count,
                    total_duration=(stats.total_duration),
                    min_duration=(stats.min_duration),
                    max_duration=(stats.max_duration),
                    last_duration=(stats.last_duration),
                )
                for name, stats in self._statistics.items()
            }

            self._result = ProfileResult(
                name=self.name,
                started_at=(self._started_at),
                finished_at=finished_at,
                duration=duration,
                entries=list(self._entries),
                statistics=statistics_copy,
                metadata=dict(self.metadata),
            )

            self._started_at = None

            return self._result

    def reset(
        self,
    ) -> None:
        """
        Reset all profiling data.
        """

        with self._lock:

            self._started_at = None

            self._result = None

            self._entries.clear()

            self._statistics.clear()

        self._set_depth(0)

    # ========================================================================
    # SECTIONS
    # ========================================================================

    def section(
        self,
        name: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProfileSection:
        """
        Create a profiling section.

        The profiler must already be running.
        """

        if not self.is_running:

            raise RuntimeError(f"Profiler '{self.name}' " "is not running.")

        normalized_name = self._normalize_name(name)

        return ProfileSection(
            self,
            normalized_name,
            metadata=metadata,
        )

    def _enter_section(
        self,
        name: str,
    ) -> int:
        """
        Increase the thread-local nesting depth.
        """

        depth = self._get_depth()

        self._set_depth(depth + 1)

        return depth

    def _exit_section(
        self,
    ) -> None:
        """
        Decrease the thread-local nesting depth.
        """

        depth = self._get_depth()

        self._set_depth(max(0, depth - 1))

    def _record_section(
        self,
        *,
        name: str,
        started_at: float,
        finished_at: float,
        duration: float,
        depth: int,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Store section timing information.
        """

        entry = ProfileEntry(
            name=name,
            started_at=started_at,
            finished_at=finished_at,
            duration=duration,
            depth=depth,
            metadata=dict(metadata),
        )

        with self._lock:

            self._entries.append(entry)

            if len(self._entries) > self._max_entries:

                overflow = len(self._entries) - self._max_entries

                del self._entries[:overflow]

            statistics = self._statistics.get(name)

            if statistics is None:

                statistics = ProfileStatistics(name=name)

                self._statistics[name] = statistics

            statistics.record(duration)

    # ========================================================================
    # STATE
    # ========================================================================

    @property
    def is_running(
        self,
    ) -> bool:

        with self._lock:

            return self._started_at is not None

    @property
    def elapsed(
        self,
    ) -> float:

        with self._lock:

            if self._started_at is not None:

                return time.perf_counter() - self._started_at

            if self._result is not None:

                return self._result.duration

            return 0.0

    @property
    def elapsed_ms(
        self,
    ) -> float:

        return self.elapsed * 1000.0

    @property
    def result(
        self,
    ) -> Optional[ProfileResult]:

        with self._lock:

            return self._result

    @property
    def entries(
        self,
    ) -> List[ProfileEntry]:

        with self._lock:

            return list(self._entries)

    def statistics(
        self,
    ) -> Dict[str, ProfileStatistics]:
        """
        Return a copy of current statistics.
        """

        with self._lock:

            return {
                name: ProfileStatistics(
                    name=stats.name,
                    count=stats.count,
                    total_duration=(stats.total_duration),
                    min_duration=(stats.min_duration),
                    max_duration=(stats.max_duration),
                    last_duration=(stats.last_duration),
                )
                for name, stats in self._statistics.items()
            }

    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================

    def __enter__(
        self,
    ) -> "Profiler":

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
    # INTERNAL HELPERS
    # ========================================================================

    def _get_depth(
        self,
    ) -> int:

        return getattr(
            self._local,
            "depth",
            0,
        )

    def _set_depth(
        self,
        value: int,
    ) -> None:

        self._local.depth = value

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:

        if not isinstance(
            name,
            str,
        ):

            raise TypeError("Profile name must " "be a string.")

        name = name.strip()

        if not name:

            raise ValueError("Profile name cannot " "be empty.")

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
# PROFILE REGISTRY
# ============================================================================


class ProfileRegistry:
    """
    Stores completed profiling results.

    This is useful for keeping recent startup, command, or agent
    execution profiles available for diagnostics.
    """

    def __init__(
        self,
        *,
        max_results: int = 100,
    ) -> None:

        if max_results < 1:

            raise ValueError("max_results must be " "at least 1.")

        self._max_results = max_results

        self._results: List[ProfileResult] = []

        self._lock = threading.RLock()

    def add(
        self,
        result: ProfileResult,
    ) -> None:
        """
        Store a completed profile result.
        """

        if not isinstance(
            result,
            ProfileResult,
        ):

            raise TypeError("result must be " "a ProfileResult.")

        with self._lock:

            self._results.append(result)

            if len(self._results) > self._max_results:

                overflow = len(self._results) - self._max_results

                del self._results[:overflow]

    def latest(
        self,
        name: Optional[str] = None,
    ) -> Optional[ProfileResult]:
        """
        Return the latest profile result.

        Optionally filter by profile name.
        """

        with self._lock:

            if name is None:

                if not self._results:

                    return None

                return self._results[-1]

            for result in reversed(self._results):

                if result.name == name:

                    return result

            return None

    def history(
        self,
        *,
        name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProfileResult]:
        """
        Return stored profile results.
        """

        with self._lock:

            results = list(self._results)

        if name is not None:

            results = [result for result in results if result.name == name]

        if limit is not None:

            if limit < 1:

                return []

            results = results[-limit:]

        return results

    def clear(
        self,
    ) -> None:
        """
        Clear all stored profiles.
        """

        with self._lock:

            self._results.clear()

    def __len__(
        self,
    ) -> int:

        with self._lock:

            return len(self._results)


# ============================================================================
# GLOBAL PROFILE REGISTRY
# ============================================================================


_default_registry = ProfileRegistry()


def get_profile_registry() -> ProfileRegistry:
    """
    Return the default Omnix profile registry.
    """

    return _default_registry


# ============================================================================
# DECORATOR
# ============================================================================


def profile_function(
    name: Optional[str] = None,
    *,
    registry: Optional[ProfileRegistry] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Callable[
    [Callable[..., T]],
    Callable[..., T],
]:
    """
    Decorator for profiling a synchronous function.

    Example:

        @profile_function(
            "command_processing"
        )
        def process_command(command):
            ...
    """

    target_registry = registry or _default_registry

    def decorator(
        function: Callable[..., T],
    ) -> Callable[..., T]:

        profile_name = name or (f"{function.__module__}." f"{function.__qualname__}")

        @functools.wraps(function)
        def wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> T:

            profiler = Profiler(
                profile_name,
                metadata=metadata,
            )

            profiler.start()

            try:

                return function(
                    *args,
                    **kwargs,
                )

            finally:

                result = profiler.stop()

                target_registry.add(result)

        return wrapper

    return decorator


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


def profile(
    name: str,
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> Profiler:
    """
    Create and start a Profiler.

    Example:

        profiler = profile(
            "agent_execution"
        )

        ...

        result = profiler.stop()
    """

    profiler = Profiler(
        name,
        metadata=metadata,
    )

    profiler.start()

    return profiler


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "ProfileEntry",
    "ProfileStatistics",
    "ProfileResult",
    "ProfileSection",
    "Profiler",
    "ProfileRegistry",
    "get_profile_registry",
    "profile_function",
    "profile",
]
