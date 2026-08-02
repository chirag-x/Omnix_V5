"""
Omnix V5
Task Scheduler

Coordinates background task execution.
"""

from __future__ import annotations

import logging

from .background_tasks import BackgroundTask
from .job_manager import JobManager
from .timers import Timer

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Main scheduler responsible for executing
    background tasks when their timers expire.
    """

    def __init__(
        self,
    ) -> None:

        self._jobs = JobManager()

        self._timers: dict[str, Timer] = {}

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
    # Job Registration
    # ---------------------------------------------------------

    def schedule(
        self,
        task: BackgroundTask,
    ) -> None:
        """
        Schedule a background task.
        """

        self._jobs.add(task)

        self._timers[task.name] = Timer(
            interval=task.interval,
            repeat=task.repeat,
        )

        logger.debug(
            "Scheduled task '%s'",
            task.name,
        )

    def unschedule(
        self,
        name: str,
    ) -> bool:
        """
        Remove a scheduled task.
        """

        self._timers.pop(
            name,
            None,
        )

        return self._jobs.remove(
            name,
        )

    # ---------------------------------------------------------
    # Execution
    # ---------------------------------------------------------

    def tick(
        self,
    ) -> None:
        """
        Execute all expired tasks.

        Intended to be called periodically
        by Omnix's main loop.
        """

        if not self._enabled:

            return

        for task in self._jobs:

            if not task.enabled:

                continue

            timer = self._timers.get(
                task.name,
            )

            if timer is None:

                continue

            if not timer.expired():

                continue

            logger.debug(
                "Executing task '%s'",
                task.name,
            )

            try:

                task.execute()

            except Exception:

                logger.exception(
                    "Task '%s' failed",
                    task.name,
                )

            if timer.repeat:

                timer.reset()

            else:

                self.unschedule(
                    task.name,
                )

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def clear(
        self,
    ) -> None:

        self._jobs.clear()

        self._timers.clear()

    @property
    def job_count(
        self,
    ) -> int:

        return self._jobs.count

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
            "jobs": self.job_count,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "TaskScheduler(" f"jobs={self.job_count}, " f"enabled={self._enabled})"
