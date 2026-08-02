"""
Omnix V5
Application Monitor

Monitors running applications and detects lifecycle events.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from system.models.application import Application

from .process_resolver import ProcessResolver

logger = logging.getLogger(__name__)


class ApplicationMonitor:
    """
    Monitors application start/stop events.

    Responsibilities
    ----------------
    • Track running applications
    • Detect newly started applications
    • Detect closed applications
    • Notify registered callbacks
    """

    def __init__(self) -> None:

        self._resolver = ProcessResolver()

        self._running: dict[int, Application] = {}

        self._start_callbacks: list[
            Callable[[Application], None]
        ] = []

        self._stop_callbacks: list[
            Callable[[Application], None]
        ] = []

    # ---------------------------------------------------------
    # Callback Registration
    # ---------------------------------------------------------

    def on_application_started(
        self,
        callback: Callable[[Application], None],
    ) -> None:

        self._start_callbacks.append(callback)

    def on_application_stopped(
        self,
        callback: Callable[[Application], None],
    ) -> None:

        self._stop_callbacks.append(callback)

    # ---------------------------------------------------------
    # Monitoring
    # ---------------------------------------------------------

    def update(
        self,
        applications: list[Application],
    ) -> None:
        """
        Update monitor state and detect changes.
        """

        previous = self._running

        current = self._resolver.resolve(applications)

        # -------------------------
        # Started
        # -------------------------

        for pid, app in current.items():

            if pid not in previous:

                logger.info(
                    "Application started: %s",
                    app.display_name,
                )

                self._notify_started(app)

        # -------------------------
        # Stopped
        # -------------------------

        for pid, app in previous.items():

            if pid not in current:

                logger.info(
                    "Application stopped: %s",
                    app.display_name,
                )

                self._notify_stopped(app)

        self._running = current

    # ---------------------------------------------------------
    # Queries
    # ---------------------------------------------------------

    def running(self) -> list[Application]:

        return list(self._running.values())

    def running_count(self) -> int:

        return len(self._running)

    def is_running(
        self,
        application: Application,
    ) -> bool:

        return application in self._running.values()

    # ---------------------------------------------------------
    # Notifications
    # ---------------------------------------------------------

    def _notify_started(
        self,
        application: Application,
    ) -> None:

        for callback in self._start_callbacks:

            try:
                callback(application)

            except Exception:

                logger.exception(
                    "Application start callback failed."
                )

    def _notify_stopped(
        self,
        application: Application,
    ) -> None:

        for callback in self._stop_callbacks:

            try:
                callback(application)

            except Exception:

                logger.exception(
                    "Application stop callback failed."
                )