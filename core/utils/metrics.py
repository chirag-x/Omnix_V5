"""
Omnix V5 - Core Metrics Utility

Lightweight, dependency-free metrics collection for Omnix V5.

Provides:
    - Counters
    - Gauges
    - Timing metrics
    - Metric snapshots
    - Thread-safe access
    - Simple statistics

Designed for use by:
    - HealthMonitor
    - OmnixEngine
    - Services
    - Planning
    - Agent execution
    - Diagnostics
"""

from __future__ import annotations

import threading
import time

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ============================================================================
# CONSTANTS
# ============================================================================


DEFAULT_MAX_SAMPLES = 1000


# ============================================================================
# METRIC DATA MODELS
# ============================================================================


@dataclass
class CounterMetric:
    """
    A monotonically increasing or manually adjusted counter.
    """

    name: str

    value: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    updated_at: float = field(default_factory=time.time)

    def increment(
        self,
        amount: float = 1.0,
    ) -> float:
        """
        Increase the counter.
        """

        self.value += float(amount)

        self.updated_at = time.time()

        return self.value

    def reset(
        self,
    ) -> None:
        """
        Reset the counter to zero.
        """

        self.value = 0.0

        self.updated_at = time.time()

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "name": self.name,
            "type": "counter",
            "value": self.value,
            "metadata": dict(self.metadata),
            "updated_at": self.updated_at,
        }


@dataclass
class GaugeMetric:
    """
    A metric representing a current value.

    Examples:
        - active tasks
        - loaded services
        - queue size
        - CPU usage
    """

    name: str

    value: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)

    updated_at: float = field(default_factory=time.time)

    def set(
        self,
        value: float,
    ) -> float:
        """
        Set the gauge value.
        """

        self.value = float(value)

        self.updated_at = time.time()

        return self.value

    def increment(
        self,
        amount: float = 1.0,
    ) -> float:
        """
        Increase the gauge.
        """

        return self.set(self.value + float(amount))

    def decrement(
        self,
        amount: float = 1.0,
    ) -> float:
        """
        Decrease the gauge.
        """

        return self.set(self.value - float(amount))

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "name": self.name,
            "type": "gauge",
            "value": self.value,
            "metadata": dict(self.metadata),
            "updated_at": self.updated_at,
        }


@dataclass
class TimingMetric:
    """
    Stores timing samples and aggregate statistics.
    """

    name: str

    samples: List[float] = field(default_factory=list)

    total_duration: float = 0.0

    count: int = 0

    min_duration: Optional[float] = None

    max_duration: Optional[float] = None

    last_duration: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    updated_at: float = field(default_factory=time.time)

    def record(
        self,
        duration: float,
        *,
        max_samples: int = (DEFAULT_MAX_SAMPLES),
    ) -> None:
        """
        Record a duration in seconds.
        """

        duration = float(duration)

        if duration < 0:

            raise ValueError("Metric duration cannot be negative.")

        self.samples.append(duration)

        if len(self.samples) > max_samples:

            overflow = len(self.samples) - max_samples

            del self.samples[:overflow]

        self.total_duration += duration

        self.count += 1

        self.last_duration = duration

        if self.min_duration is None or duration < self.min_duration:

            self.min_duration = duration

        if self.max_duration is None or duration > self.max_duration:

            self.max_duration = duration

        self.updated_at = time.time()

    @property
    def average_duration(
        self,
    ) -> float:

        if self.count == 0:

            return 0.0

        return self.total_duration / self.count

    @property
    def last_duration_ms(
        self,
    ) -> Optional[float]:

        if self.last_duration is None:

            return None

        return self.last_duration * 1000.0

    @property
    def average_duration_ms(
        self,
    ) -> float:

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

    def to_dict(
        self,
        *,
        include_samples: bool = False,
    ) -> Dict[str, Any]:

        data = {
            "name": self.name,
            "type": "timing",
            "count": self.count,
            "total_duration": (self.total_duration),
            "average_duration": (self.average_duration),
            "min_duration": (self.min_duration),
            "max_duration": (self.max_duration),
            "last_duration": (self.last_duration),
            "average_duration_ms": (self.average_duration_ms),
            "min_duration_ms": (self.min_duration_ms),
            "max_duration_ms": (self.max_duration_ms),
            "last_duration_ms": (self.last_duration_ms),
            "metadata": dict(self.metadata),
            "updated_at": self.updated_at,
        }

        if include_samples:

            data["samples"] = list(self.samples)

        return data


# ============================================================================
# METRICS REGISTRY
# ============================================================================


class MetricsRegistry:
    """
    Thread-safe central registry for Omnix metrics.

    Example:

        metrics = MetricsRegistry()

        metrics.increment(
            "commands.total"
        )

        metrics.set_gauge(
            "tasks.active",
            3,
        )

        metrics.record_timing(
            "skill.execution",
            0.42,
        )
    """

    def __init__(
        self,
        *,
        max_timing_samples: int = (DEFAULT_MAX_SAMPLES),
    ) -> None:

        if max_timing_samples < 1:

            raise ValueError("max_timing_samples " "must be at least 1.")

        self._max_timing_samples = max_timing_samples

        self._counters: Dict[str, CounterMetric] = {}

        self._gauges: Dict[str, GaugeMetric] = {}

        self._timings: Dict[str, TimingMetric] = {}

        self._lock = threading.RLock()

        self._created_at = time.time()

    # ========================================================================
    # COUNTERS
    # ========================================================================

    def increment(
        self,
        name: str,
        amount: float = 1.0,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Increment a counter and return its new value.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._counters.get(name)

            if metric is None:

                metric = CounterMetric(
                    name=name,
                    metadata=dict(metadata or {}),
                )

                self._counters[name] = metric

            elif metadata:

                metric.metadata.update(metadata)

            return metric.increment(amount)

    def get_counter(
        self,
        name: str,
        default: float = 0.0,
    ) -> float:
        """
        Return a counter value.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._counters.get(name)

            if metric is None:

                return float(default)

            return metric.value

    def reset_counter(
        self,
        name: str,
    ) -> bool:
        """
        Reset an existing counter.

        Returns False if the counter does not exist.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._counters.get(name)

            if metric is None:

                return False

            metric.reset()

            return True

    # ========================================================================
    # GAUGES
    # ========================================================================

    def set_gauge(
        self,
        name: str,
        value: float,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Set a gauge value.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._gauges.get(name)

            if metric is None:

                metric = GaugeMetric(
                    name=name,
                    metadata=dict(metadata or {}),
                )

                self._gauges[name] = metric

            elif metadata:

                metric.metadata.update(metadata)

            return metric.set(value)

    def increment_gauge(
        self,
        name: str,
        amount: float = 1.0,
    ) -> float:
        """
        Increase a gauge.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._gauges.get(name)

            if metric is None:

                metric = GaugeMetric(name=name)

                self._gauges[name] = metric

            return metric.increment(amount)

    def decrement_gauge(
        self,
        name: str,
        amount: float = 1.0,
    ) -> float:
        """
        Decrease a gauge.
        """

        return self.increment_gauge(
            name,
            -float(amount),
        )

    def get_gauge(
        self,
        name: str,
        default: float = 0.0,
    ) -> float:
        """
        Return a gauge value.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._gauges.get(name)

            if metric is None:

                return float(default)

            return metric.value

    # ========================================================================
    # TIMINGS
    # ========================================================================

    def record_timing(
        self,
        name: str,
        duration: float,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TimingMetric:
        """
        Record a duration in seconds.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._timings.get(name)

            if metric is None:

                metric = TimingMetric(
                    name=name,
                    metadata=dict(metadata or {}),
                )

                self._timings[name] = metric

            elif metadata:

                metric.metadata.update(metadata)

            metric.record(
                duration,
                max_samples=(self._max_timing_samples),
            )

            return metric

    def get_timing(
        self,
        name: str,
    ) -> Optional[TimingMetric]:
        """
        Get a copy of a timing metric.
        """

        name = self._normalize_name(name)

        with self._lock:

            metric = self._timings.get(name)

            if metric is None:

                return None

            return TimingMetric(
                name=metric.name,
                samples=list(metric.samples),
                total_duration=(metric.total_duration),
                count=metric.count,
                min_duration=(metric.min_duration),
                max_duration=(metric.max_duration),
                last_duration=(metric.last_duration),
                metadata=dict(metric.metadata),
                updated_at=(metric.updated_at),
            )

    # ========================================================================
    # SNAPSHOTS
    # ========================================================================

    def snapshot(
        self,
        *,
        include_timing_samples: bool = (False),
    ) -> Dict[str, Any]:
        """
        Return a complete metrics snapshot.
        """

        with self._lock:

            return {
                "created_at": (self._created_at),
                "captured_at": (time.time()),
                "counters": {
                    name: metric.to_dict() for name, metric in self._counters.items()
                },
                "gauges": {
                    name: metric.to_dict() for name, metric in self._gauges.items()
                },
                "timings": {
                    name: metric.to_dict(include_samples=(include_timing_samples))
                    for name, metric in self._timings.items()
                },
            }

    def summary(
        self,
    ) -> Dict[str, Any]:
        """
        Return a lightweight metrics summary.
        """

        with self._lock:

            return {
                "counter_count": len(self._counters),
                "gauge_count": len(self._gauges),
                "timing_count": len(self._timings),
                "uptime_seconds": (time.time() - self._created_at),
            }

    # ========================================================================
    # MANAGEMENT
    # ========================================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all metrics.
        """

        with self._lock:

            self._counters.clear()

            self._gauges.clear()

            self._timings.clear()

            self._created_at = time.time()

    def remove(
        self,
        name: str,
    ) -> bool:
        """
        Remove a metric by name.

        Searches counters, gauges, and timing metrics.
        """

        name = self._normalize_name(name)

        removed = False

        with self._lock:

            if name in self._counters:

                del self._counters[name]

                removed = True

            if name in self._gauges:

                del self._gauges[name]

                removed = True

            if name in self._timings:

                del self._timings[name]

                removed = True

        return removed

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        """
        Validate and normalize a metric name.
        """

        if not isinstance(
            name,
            str,
        ):

            raise TypeError("Metric name must be " "a string.")

        name = name.strip()

        if not name:

            raise ValueError("Metric name cannot " "be empty.")

        return name


# ============================================================================
# GLOBAL METRICS REGISTRY
# ============================================================================


_default_metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """
    Return the default Omnix metrics registry.
    """

    return _default_metrics


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def increment_metric(
    name: str,
    amount: float = 1.0,
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Increment a counter in the default registry.
    """

    return _default_metrics.increment(
        name,
        amount,
        metadata=metadata,
    )


def set_metric(
    name: str,
    value: float,
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Set a gauge in the default registry.
    """

    return _default_metrics.set_gauge(
        name,
        value,
        metadata=metadata,
    )


def record_metric_timing(
    name: str,
    duration: float,
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> TimingMetric:
    """
    Record timing data in the default registry.
    """

    return _default_metrics.record_timing(
        name,
        duration,
        metadata=metadata,
    )


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "DEFAULT_MAX_SAMPLES",
    "CounterMetric",
    "GaugeMetric",
    "TimingMetric",
    "MetricsRegistry",
    "get_metrics",
    "increment_metric",
    "set_metric",
    "record_metric_timing",
]
