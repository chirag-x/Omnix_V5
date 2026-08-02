"""
Omnix V5
Application Controller

Low-level OS application operations.
"""

from __future__ import annotations

import logging
import subprocess

import psutil

logger = logging.getLogger(__name__)


class AppController:
    """
    Low-level application service.

    Handles direct interaction with the OS.
    Does not contain application intelligence.
    """

    def __init__(self) -> None:

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
    # Launch
    # ---------------------------------------------------------

    def launch(
        self,
        executable: str,
        *arguments: str,
    ) -> bool:
        """
        Launch executable directly.
        """

        if not self._enabled:

            return False

        try:

            subprocess.Popen(
                [
                    executable,
                    *arguments,
                ],
                shell=False,
            )

            logger.info(
                "Started application: %s",
                executable,
            )

            return True

        except Exception as exc:

            logger.error(
                "Launch failed %s: %s",
                executable,
                exc,
            )

            return False

    # ---------------------------------------------------------
    # Process Operations
    # ---------------------------------------------------------

    def terminate(
        self,
        pid: int,
    ) -> bool:
        """
        Terminate process by PID.
        """

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
        """
        Force kill process.
        """

        try:

            process = psutil.Process(pid)

            process.kill()

            return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            return False

    def is_running(
        self,
        pid: int,
    ) -> bool:
        """
        Check process state.
        """

        try:

            return psutil.pid_exists(pid)

        except Exception:

            return False

    # ---------------------------------------------------------
    # Information
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

        return "AppController(" f"enabled={self._enabled})"
