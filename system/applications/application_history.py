"""
Omnix V5
Application History

Tracks application launch history and usage.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime

from system.models.application import Application

logger = logging.getLogger(__name__)


class ApplicationHistory:
    """
    Tracks application launch history.
    """

    def __init__(self) -> None:

        self._history: list[tuple[datetime, Application]] = []

        self._launch_counter: Counter[str] = Counter()

    # ---------------------------------------------------------
    # Recording
    # ---------------------------------------------------------

    def record_launch(
        self,
        application: Application,
    ) -> None:
        """
        Record an application launch.
        """

        self._history.append(
            (
                datetime.now(),
                application,
            )
        )

        self._launch_counter[
            application.name.lower()
        ] += 1

        logger.info(
            "Recorded launch: %s",
            application.display_name,
        )

    # ---------------------------------------------------------
    # Queries
    # ---------------------------------------------------------

    def history(self) -> list[tuple[datetime, Application]]:
        """
        Return launch history.
        """

        return list(self._history)

    def recent(
        self,
        limit: int = 10,
    ) -> list[Application]:
        """
        Return recently launched applications.
        """

        return [
            app
            for _, app in reversed(self._history[-limit:])
        ]

    def launch_count(
        self,
        application: Application,
    ) -> int:

        return self._launch_counter[
            application.name.lower()
        ]

    def most_used(
        self,
        limit: int = 10,
    ) -> list[tuple[str, int]]:
        """
        Return the most frequently launched applications.
        """

        return self._launch_counter.most_common(limit)

    # ---------------------------------------------------------
    # Maintenance
    # ---------------------------------------------------------

    def clear(self) -> None:

        self._history.clear()

        self._launch_counter.clear()

        logger.info("Application history cleared.")

    @property
    def count(self) -> int:

        return len(self._history)