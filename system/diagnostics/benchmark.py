"""
Omnix V5
Benchmark

Performance measurement utilities.
"""

from __future__ import annotations

import logging
import time

from datetime import datetime

logger = logging.getLogger(__name__)


class Benchmark:
    """
    Measures execution performance.
    """

    def __init__(
        self,
    ) -> None:

        self._results: list[dict] = []

    # ---------------------------------------------------------
    # Timing
    # ---------------------------------------------------------

    def measure(
        self,
        name: str,
        function,
        *args,
        **kwargs,
    ) -> dict:

        start = time.perf_counter()

        success = True

        error = None

        result = None

        try:

            result = function(
                *args,
                **kwargs,
            )

        except Exception as exc:

            success = False

            error = str(exc)

            logger.exception(
                "Benchmark failed: %s",
                name,
            )

        duration = (time.perf_counter() - start) * 1000

        benchmark = {
            "name": name,
            "duration_ms": duration,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if result is not None:

            benchmark["result_type"] = type(result).__name__

        if error:

            benchmark["error"] = error

        self._results.append(
            benchmark,
        )

        return benchmark

    # ---------------------------------------------------------
    # Manual Timing
    # ---------------------------------------------------------

    def start(
        self,
    ) -> float:

        return time.perf_counter()

    def stop(
        self,
        start_time: float,
    ) -> float:

        return (time.perf_counter() - start_time) * 1000

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    def results(
        self,
    ) -> list[dict]:

        return self._results.copy()

    def latest(
        self,
    ) -> dict | None:

        return self._results[-1] if self._results else None

    def clear(
        self,
    ) -> None:

        self._results.clear()

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "benchmarks": len(self._results),
            "average_ms": self.average_time(),
            "fastest_ms": self.fastest_time(),
            "slowest_ms": self.slowest_time(),
        }

    def average_time(
        self,
    ) -> float:

        if not self._results:

            return 0.0

        return sum(item["duration_ms"] for item in self._results) / len(self._results)

    def fastest_time(
        self,
    ) -> float:

        if not self._results:

            return 0.0

        return min(item["duration_ms"] for item in self._results)

    def slowest_time(
        self,
    ) -> float:

        if not self._results:

            return 0.0

        return max(item["duration_ms"] for item in self._results)

    def __repr__(
        self,
    ) -> str:

        return "Benchmark(" f"tests={len(self._results)})"
