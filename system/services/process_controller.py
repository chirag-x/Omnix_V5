"""
Omnix V5
Process Controller

Low-level process operations.
"""

from __future__ import annotations

import logging

import psutil

logger = logging.getLogger(__name__)


class ProcessController:
    """
    Direct OS process control service.
    """

    def __init__(
        self,
    ) -> None:

        self._enabled = True

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def enabled(
        self,
    ) -> bool:

        return self._enabled

    def enable(
        self,
    ) -> None:

        self._enabled = True

    def disable(
        self,
    ) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Process Control
    # ---------------------------------------------------------

    def terminate(
        self,
        pid: int,
    ) -> bool:

        if not self._enabled:

            return False

        try:

            process = psutil.Process(pid)

            process.terminate()

            return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            return False

    def kill(
        self,
        pid: int,
    ) -> bool:

        if not self._enabled:

            return False

        try:

            process = psutil.Process(pid)

            process.kill()

            return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            return False

    def suspend(
        self,
        pid: int,
    ) -> bool:

        try:

            process = psutil.Process(pid)

            process.suspend()

            return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            return False

    def resume(
        self,
        pid: int,
    ) -> bool:

        try:

            process = psutil.Process(pid)

            process.resume()

            return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            return False

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def cpu_usage(
        self,
        pid: int,
    ) -> float | None:

        try:

            return psutil.Process(pid).cpu_percent()

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            return None

    def memory_usage(
        self,
        pid: int,
    ) -> int | None:

        try:

            return psutil.Process(pid).memory_info().rss

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            return None

    def exists(
        self,
        pid: int,
    ) -> bool:

        return psutil.pid_exists(
            pid,
        )

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
        }

    def __repr__(
        self,
    ) -> str:

        return "ProcessController(" f"enabled={self._enabled})"
