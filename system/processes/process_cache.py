"""
Omnix V5
Process Cache
"""

from __future__ import annotations

import logging
from datetime import datetime

from system.models.process import Process

logger = logging.getLogger(__name__)


class ProcessCache:
    """
    Fast in-memory cache for Process objects.

    Responsibilities
    ----------------
    • Store Process models
    • Fast PID lookup
    • Name searching
    • Cache updates

    This class NEVER scans the operating system.
    """

    def __init__(self) -> None:

        self._cache: dict[int, Process] = {}

        self._last_updated: datetime | None = None

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def count(self) -> int:
        """Number of cached processes."""
        return len(self._cache)

    @property
    def last_updated(self) -> datetime | None:
        """Last cache update."""
        return self._last_updated

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def update(
        self,
        processes: dict[int, Process],
    ) -> None:
        """
        Replace the cache with a new process collection.
        """

        self._cache = dict(processes)

        self._last_updated = datetime.now()

        logger.info(
            "Cached %d processes.",
            len(self._cache),
        )

    def add(
        self,
        process: Process,
    ) -> None:
        """
        Add one process.
        """

        self._cache[process.pid] = process

    def remove(
        self,
        pid: int,
    ) -> None:
        """
        Remove one process.
        """

        self._cache.pop(pid, None)

    def clear(self) -> None:
        """
        Clear cache.
        """

        self._cache.clear()

        self._last_updated = None

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def get(
        self,
        pid: int,
    ) -> Process | None:
        """
        Get process by PID.
        """

        return self._cache.get(pid)

    def all(self) -> dict[int, Process]:
        """
        Return all cached processes.
        """

        return dict(self._cache)

    def pids(self) -> list[int]:
        """
        Return cached PIDs.
        """

        return sorted(self._cache.keys())

    def exists(
        self,
        pid: int,
    ) -> bool:
        """
        Check whether PID exists.
        """

        return pid in self._cache

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        text: str,
    ) -> list[Process]:
        """
        Search processes by name.
        """

        text = text.lower()

        results = []

        for process in self._cache.values():

            if text in process.name.lower():

                results.append(process)

        return results

    def by_username(
        self,
        username: str,
    ) -> list[Process]:
        """
        Return all processes for a user.
        """

        username = username.lower()

        return [
            process
            for process in self._cache.values()
            if process.username.lower() == username
        ]

    def by_status(
        self,
        status: str,
    ) -> list[Process]:
        """
        Return all processes with a status.
        """

        status = status.lower()

        return [
            process
            for process in self._cache.values()
            if process.status.lower() == status
        ]

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(self) -> dict:
        """
        Cache statistics.
        """

        return {
            "count": self.count,
            "last_updated": self.last_updated,
        }

    # ---------------------------------------------------------
    # Magic Methods
    # ---------------------------------------------------------

    def __contains__(
        self,
        pid: int,
    ) -> bool:

        return pid in self._cache

    def __len__(self) -> int:

        return len(self._cache)

    def __iter__(self):

        return iter(self._cache.values())

    def __repr__(self) -> str:

        return f"{self.__class__.__name__}" f"(count={self.count})"
