"""
Omnix V5
Process Resolver

Maps running system processes to Application models.
"""

from __future__ import annotations

import logging

import psutil

from system.models.application import Application

logger = logging.getLogger(__name__)


class ProcessResolver:
    """
    Resolves running processes into Application models.
    """

    def __init__(self) -> None:

        self._running: dict[int, Application] = {}

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def resolve(
        self,
        applications: list[Application],
    ) -> dict[int, Application]:
        """
        Resolve currently running applications.

        Returns
        -------
        dict[pid, Application]
        """

        self._running.clear()

        lookup = {
            app.name.lower(): app
            for app in applications
        }

        for process in psutil.process_iter(
            [
                "pid",
                "name",
                "exe",
            ]
        ):

            try:

                pid = process.info["pid"]

                exe = process.info["exe"]

                name = process.info["name"]

                app = self._match(
                    lookup,
                    name,
                    exe,
                )

                if app is not None:
                    self._running[pid] = app

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                continue

            except Exception:

                logger.exception(
                    "Failed resolving process."
                )

        logger.info(
            "Resolved %d running applications.",
            len(self._running),
        )

        return self._running

    def get_running(self) -> list[Application]:
        """
        Return running applications.
        """

        return list(self._running.values())

    def is_running(
        self,
        application: Application,
    ) -> bool:

        return application in self._running.values()

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _match(
        self,
        lookup: dict[str, Application],
        process_name: str | None,
        executable: str | None,
    ) -> Application | None:

        if process_name:

            key = process_name.removesuffix(".exe").lower()

            if key in lookup:
                return lookup[key]

        if executable:

            key = executable.split("\\")[-1]

            key = key.removesuffix(".exe").lower()

            if key in lookup:
                return lookup[key]

        return None