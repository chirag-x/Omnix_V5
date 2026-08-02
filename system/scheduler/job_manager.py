"""
Omnix V5
Job Manager

Manages scheduled background tasks.
"""

from __future__ import annotations

import logging

from .background_tasks import BackgroundTask

logger = logging.getLogger(__name__)


class JobManager:
    """
    Stores and manages scheduled background tasks.
    """

    def __init__(
        self,
    ) -> None:

        self._jobs: dict[str, BackgroundTask] = {}

    # ---------------------------------------------------------
    # Job Management
    # ---------------------------------------------------------

    def add(
        self,
        task: BackgroundTask,
    ) -> None:
        """
        Register a background task.
        """

        self._jobs[task.name] = task

        logger.debug(
            "Added background task '%s'",
            task.name,
        )

    def remove(
        self,
        name: str,
    ) -> bool:
        """
        Remove a background task.
        """

        if name in self._jobs:

            del self._jobs[name]

            logger.debug(
                "Removed background task '%s'",
                name,
            )

            return True

        return False

    def get(
        self,
        name: str,
    ) -> BackgroundTask | None:
        """
        Retrieve a task by name.
        """

        return self._jobs.get(name)

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        Check if a task exists.
        """

        return name in self._jobs

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def all(
        self,
    ) -> list[BackgroundTask]:
        """
        Return all registered tasks.
        """

        return list(self._jobs.values())

    def clear(
        self,
    ) -> None:
        """
        Remove all registered tasks.
        """

        self._jobs.clear()

    @property
    def count(
        self,
    ) -> int:

        return len(self._jobs)

    def statistics(
        self,
    ) -> dict:

        enabled = sum(task.enabled for task in self._jobs.values())

        return {
            "jobs": self.count,
            "enabled": enabled,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __len__(
        self,
    ) -> int:

        return self.count

    def __iter__(
        self,
    ):

        return iter(
            self._jobs.values(),
        )

    def __repr__(
        self,
    ) -> str:

        return "JobManager(" f"jobs={self.count})"
