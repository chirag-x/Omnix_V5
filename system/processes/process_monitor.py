"""
Omnix V5
Process Monitor
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from system.models.process import Process

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """
    Monitors process lifecycle.

    Responsibilities
    ----------------
    • Detect process start
    • Detect process exit
    • Maintain running process snapshot
    • Notify callbacks

    This class NEVER scans the operating system.
    """

    def __init__(self) -> None:

        self._running: dict[int, Process] = {}

        self._start_callbacks: list[Callable[[Process], None]] = []

        self._stop_callbacks: list[Callable[[Process], None]] = []

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def count(self) -> int:
        """
        Number of running processes.
        """

        return len(self._running)

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update(
        self,
        processes: dict[int, Process],
    ) -> None:
        """
        Compare current snapshot with previous snapshot.
        """

        previous = set(self._running.keys())

        current = set(processes.keys())

        started = current - previous

        stopped = previous - current

        for pid in started:

            process = processes[pid]

            self._running[pid] = process

            logger.info(
                "Process started: %s (%d)",
                process.name,
                pid,
            )

            self._notify_started(process)

        for pid in stopped:

            process = self._running.pop(pid)

            logger.info(
                "Process stopped: %s (%d)",
                process.name,
                pid,
            )

            self._notify_stopped(process)

        for pid in current & previous:

            self._running[pid] = processes[pid]

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def on_started(
        self,
        callback: Callable[[Process], None],
    ) -> None:
        """
        Register process start callback.
        """

        self._start_callbacks.append(callback)

    def on_stopped(
        self,
        callback: Callable[[Process], None],
    ) -> None:
        """
        Register process stop callback.
        """

        self._stop_callbacks.append(callback)

    def _notify_started(
        self,
        process: Process,
    ) -> None:

        for callback in self._start_callbacks:

            try:

                callback(process)

            except Exception:

                logger.exception("Process start callback failed.")

    def _notify_stopped(
        self,
        process: Process,
    ) -> None:

        for callback in self._stop_callbacks:

            try:

                callback(process)

            except Exception:

                logger.exception("Process stop callback failed.")

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def running(self) -> dict[int, Process]:
        """
        Return running processes.
        """

        return dict(self._running)

    def get(
        self,
        pid: int,
    ) -> Process | None:
        """
        Return one running process.
        """

        return self._running.get(pid)

    def exists(
        self,
        pid: int,
    ) -> bool:
        """
        Check whether PID is running.
        """

        return pid in self._running

    def clear(self) -> None:
        """
        Clear monitor state.
        """

        self._running.clear()

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(self) -> dict:

        return {
            "running": self.count,
            "start_callbacks": len(self._start_callbacks),
            "stop_callbacks": len(self._stop_callbacks),
        }

    # ---------------------------------------------------------
    # Magic Methods
    # ---------------------------------------------------------

    def __len__(self) -> int:

        return self.count

    def __contains__(
        self,
        pid: int,
    ) -> bool:

        return pid in self._running

    def __repr__(self) -> str:

        return f"{self.__class__.__name__}" f"(running={self.count})"
