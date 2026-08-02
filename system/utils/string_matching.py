"""
Omnix V5
Timer Utilities

Time measurement helpers.
"""

from __future__ import annotations

import time

from datetime import datetime


class Timer:
    """
    Simple execution timer.
    """

    def __init__(
        self,
    ) -> None:

        self._start = None

        self._end = None

    # ---------------------------------------------------------
    # Start
    # ---------------------------------------------------------

    def start(
        self,
    ) -> None:

        self._start = time.perf_counter()

        self._end = None

    # ---------------------------------------------------------
    # Stop
    # ---------------------------------------------------------

    def stop(
        self,
    ) -> float:

        if self._start is None:

            return 0.0

        self._end = time.perf_counter()

        return self.elapsed()

    # ---------------------------------------------------------
    # Elapsed
    # ---------------------------------------------------------

    def elapsed(
        self,
    ) -> float:

        if self._start is None:

            return 0.0

        end = self._end if self._end else time.perf_counter()

        return end - self._start

    def elapsed_ms(
        self,
    ) -> float:

        return self.elapsed() * 1000

    # ---------------------------------------------------------
    # Context Manager
    # ---------------------------------------------------------

    def __enter__(
        self,
    ):

        self.start()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.stop()

    def __repr__(
        self,
    ) -> str:

        return "Timer(" f"elapsed={self.elapsed_ms():.2f}ms)"


# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------


def current_time() -> str:
    """
    Return current timestamp.
    """

    return datetime.utcnow().isoformat()


def sleep(
    seconds: float,
) -> None:
    """
    Safe delay.
    """

    time.sleep(
        seconds,
    )
