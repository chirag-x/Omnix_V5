"""
Omnix V5
Process Finder
"""

from __future__ import annotations

import logging

from system.models.process import Process
from .process_cache import ProcessCache

logger = logging.getLogger(__name__)


class ProcessFinder:
    """
    Finds processes from the ProcessCache.

    Responsibilities
    ----------------
    • PID lookup
    • Name lookup
    • Executable lookup
    • Parent lookup
    • Command line lookup

    This class NEVER scans the operating system.
    """

    def __init__(
        self,
        cache: ProcessCache,
    ) -> None:

        self._cache = cache

    # ---------------------------------------------------------
    # Basic Lookup
    # ---------------------------------------------------------

    def by_pid(
        self,
        pid: int,
    ) -> Process | None:
        """
        Find process by PID.
        """

        return self._cache.get(pid)

    def by_name(
        self,
        name: str,
    ) -> list[Process]:
        """
        Find processes by name.
        """

        name = name.lower()

        return [process for process in self._cache if process.name.lower() == name]

    def contains(
        self,
        pid: int,
    ) -> bool:
        """
        Check whether a PID exists.
        """

        return pid in self._cache

    # ---------------------------------------------------------
    # Executable
    # ---------------------------------------------------------

    def by_executable(
        self,
        executable: str,
    ) -> list[Process]:
        """
        Find processes by executable path.
        """

        executable = executable.lower()

        return [
            process
            for process in self._cache
            if process.executable.lower() == executable
        ]

    def by_working_directory(
        self,
        directory: str,
    ) -> list[Process]:
        """
        Find processes by working directory.
        """

        directory = directory.lower()

        return [
            process
            for process in self._cache
            if process.working_directory.lower() == directory
        ]

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    def children(
        self,
        pid: int,
    ) -> list[Process]:
        """
        Return child processes.
        """

        return [process for process in self._cache if process.parent_pid == pid]

    def parent(
        self,
        pid: int,
    ) -> Process | None:
        """
        Return parent process.
        """

        process = self.by_pid(pid)

        if process is None:
            return None

        return self.by_pid(process.parent_pid)

    # ---------------------------------------------------------
    # Command Line
    # ---------------------------------------------------------

    def by_command(
        self,
        text: str,
    ) -> list[Process]:
        """
        Search command line arguments.
        """

        text = text.lower()

        results = []

        for process in self._cache:

            command = " ".join(process.command_line).lower()

            if text in command:
                results.append(process)

        return results

    def fuzzy(
        self,
        text: str,
    ) -> list[Process]:
        """
        Fuzzy name search.
        """

        return self._cache.search(text)

    # ---------------------------------------------------------
    # Filters
    # ---------------------------------------------------------

    def by_username(
        self,
        username: str,
    ) -> list[Process]:

        return self._cache.by_username(username)

    def by_status(
        self,
        status: str,
    ) -> list[Process]:

        return self._cache.by_status(status)

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(self) -> dict:

        return {
            "processes": self._cache.count,
        }

    def __repr__(self) -> str:

        return f"{self.__class__.__name__}" f"(processes={self._cache.count})"
