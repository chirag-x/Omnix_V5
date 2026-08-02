"""
Omnix V5
Process Detector

Detects running processes from the operating system.
"""

from __future__ import annotations

import logging
from datetime import datetime

import psutil

from system.models.process import Process

logger = logging.getLogger(__name__)


class ProcessDetector:
    """
    Detects running operating system processes.

    Responsibilities
    ----------------
    • Enumerate running processes
    • Convert psutil objects into Process models
    • Handle inaccessible processes
    • Return PID-indexed process dictionary

    This class DOES NOT:
        • Cache processes
        • Monitor changes
        • Kill processes
        • Search processes
    """

    PROCESS_ATTRIBUTES = (
        "pid",
        "ppid",
        "name",
        "exe",
        "cwd",
        "cmdline",
        "username",
        "status",
        "create_time",
        "cpu_percent",
        "memory_percent",
    )

    def __init__(self) -> None:

        self._processes: dict[int, Process] = {}

        self._last_scan: datetime | None = None

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def last_scan(self) -> datetime | None:
        """Time of the most recent process scan."""
        return self._last_scan

    @property
    def count(self) -> int:
        """Number of detected processes."""
        return len(self._processes)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def detect(self) -> dict[int, Process]:
        """
        Detect all running processes.

        Returns
        -------
        dict[int, Process]
        """

        logger.info("Scanning running processes...")

        self._processes.clear()

        for process in psutil.process_iter(self.PROCESS_ATTRIBUTES):

            try:

                model = self._build_process(process)

                if model is not None:
                    self._processes[model.pid] = model

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

            except Exception:

                logger.exception("Unexpected process detection error.")

        self._last_scan = datetime.now()

        logger.info(
            "Detected %d running processes.",
            len(self._processes),
        )

        return self._processes

    def refresh(self) -> dict[int, Process]:
        """
        Refresh process list.
        """

        return self.detect()

    def get_processes(self) -> dict[int, Process]:
        """
        Return cached processes.
        """

        return dict(self._processes)

    def get_process(
        self,
        pid: int,
    ) -> Process | None:
        """
        Return one cached process.
        """

        return self._processes.get(pid)

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _build_process(
        self,
        process: psutil.Process,
    ) -> Process | None:
        """
        Convert a psutil.Process into a Process model.
        """

        info = process.info

        try:

            create_time = info.get("create_time")

            started_at = datetime.fromtimestamp(create_time) if create_time else None

            return Process(
                pid=info.get("pid", 0),
                parent_pid=info.get("ppid", 0),
                name=info.get("name") or "",
                executable=info.get("exe") or "",
                working_directory=info.get("cwd") or "",
                command_line=info.get("cmdline") or [],
                username=info.get("username") or "",
                status=info.get("status") or "",
                cpu_percent=float(info.get("cpu_percent") or 0.0),
                memory_percent=float(info.get("memory_percent") or 0.0),
                started_at=started_at,
            )

        except Exception:

            logger.exception("Failed creating Process model.")

            return None

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def exists(
        self,
        pid: int,
    ) -> bool:
        """
        Check whether a process exists.
        """

        return pid in self._processes

    def pids(self) -> list[int]:
        """
        Return all detected process IDs.
        """

        return sorted(self._processes.keys())

    def clear(self) -> None:
        """
        Clear the process cache.
        """

        self._processes.clear()

        self._last_scan = None
