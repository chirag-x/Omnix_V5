"""
Omnix V5
Process Manager
"""

from __future__ import annotations

import logging
from threading import RLock

from .process_detector import ProcessDetector
from system.models.process import Process
from .process_cache import ProcessCache
from .process_finder import ProcessFinder
from .process_monitor import ProcessMonitor
from .service_manager import ServiceManager
from .startup_manager import StartupManager

logger = logging.getLogger(__name__)


class ProcessManager:
    """
    Central entry point for the Processes subsystem.

    Responsibilities
    ----------------
    • Detect running processes
    • Cache processes
    • Find processes
    • Monitor process lifecycle
    • Manage Windows services
    • Manage startup applications

    Other Omnix modules should communicate with this class
    instead of directly using ProcessDetector or ProcessCache.
    """

    def __init__(
        self,
        controller=None,
        detector=None,
        cache=None,
        monitor=None,
        services=None,
        startup=None,
    ):

        self._initialized = False

        self._lock = RLock()

        # Core Components

        self._controller = controller

        self._detector = detector or ProcessDetector()

        self._cache = cache or ProcessCache()

        self._monitor = monitor or ProcessMonitor()

        self._services = services or ServiceManager()

        self._startup = startup or StartupManager()

        self._finder = ProcessFinder(
            self._cache,
        )

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def initialized(self) -> bool:
        """
        Returns whether the subsystem is initialized.
        """

        return self._initialized

    @property
    def process_count(self) -> int:
        """
        Number of cached processes.
        """

        return self._cache.count

    @property
    def running_count(self) -> int:
        """
        Number of monitored running processes.
        """

        return self._monitor.count

    @property
    def last_scan(self):

        return self._detector.last_scan

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def initialize(self) -> None:
        """
        Initialize the Processes subsystem.
        """

        with self._lock:

            if self._initialized:
                return

            logger.info("Initializing Process Manager...")

            processes = self._detector.detect()

            self._cache.update(
                processes,
            )

            self._monitor.update(
                processes,
            )

            self._initialized = True

            logger.info("Process Manager initialized.")

    def shutdown(self) -> None:
        """
        Shutdown the subsystem.
        """

        with self._lock:

            if not self._initialized:
                return

            logger.info("Shutting down Process Manager...")

            self._monitor.clear()

            self._cache.clear()

            self._initialized = False

    def refresh(self) -> None:
        """
        Refresh running process information.
        """

        self._ensure_initialized()

        processes = self._detector.detect()

        self._cache.update(
            processes,
        )

        self._monitor.update(
            processes,
        )

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _ensure_initialized(self) -> None:

        if not self._initialized:

            raise RuntimeError("ProcessManager is not initialized.")

    # ---------------------------------------------------------
    # Process Access
    # ---------------------------------------------------------

    def get_process(
        self,
        pid: int,
    ) -> Process | None:
        """
        Return a process by PID.
        """

        self._ensure_initialized()

        return self._finder.by_pid(pid)

    def get_processes(
        self,
    ) -> dict[int, Process]:
        """
        Return all cached processes.
        """

        self._ensure_initialized()

        return self._cache.all()

    def pids(
        self,
    ) -> list[int]:
        """
        Return all cached PIDs.
        """

        self._ensure_initialized()

        return self._cache.pids()

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

        self._ensure_initialized()

        return self._finder.fuzzy(text)

    def by_name(
        self,
        name: str,
    ) -> list[Process]:

        self._ensure_initialized()

        return self._finder.by_name(name)

    def by_executable(
        self,
        executable: str,
    ) -> list[Process]:

        self._ensure_initialized()

        return self._finder.by_executable(
            executable,
        )

    def by_username(
        self,
        username: str,
    ) -> list[Process]:

        self._ensure_initialized()

        return self._finder.by_username(
            username,
        )

    def by_status(
        self,
        status: str,
    ) -> list[Process]:

        self._ensure_initialized()

        return self._finder.by_status(
            status,
        )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    def children(
        self,
        pid: int,
    ) -> list[Process]:

        self._ensure_initialized()

        return self._finder.children(pid)

    def parent(
        self,
        pid: int,
    ) -> Process | None:

        self._ensure_initialized()

        return self._finder.parent(pid)

    def exists(
        self,
        pid: int,
    ) -> bool:

        self._ensure_initialized()

        return self._finder.contains(pid)

    # ---------------------------------------------------------
    # Monitoring
    # ---------------------------------------------------------

    def update_monitor(
        self,
    ) -> None:
        """
        Update process monitor.
        """

        self._ensure_initialized()

        self._monitor.update(
            self._cache.all(),
        )

    def on_process_started(
        self,
        callback,
    ) -> None:

        self._monitor.on_started(
            callback,
        )

    def on_process_stopped(
        self,
        callback,
    ) -> None:

        self._monitor.on_stopped(
            callback,
        )

    # ---------------------------------------------------------
    # Advanced Managers
    # ---------------------------------------------------------

    @property
    def services(
        self,
    ) -> ServiceManager:

        return self._services

    @property
    def startup(
        self,
    ) -> StartupManager:

        return self._startup

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:
        """
        Return subsystem statistics.
        """

        self._ensure_initialized()

        return {
            "initialized": self._initialized,
            "cached_processes": self._cache.count,
            "running_processes": self._monitor.count,
            "last_scan": self.last_scan,
        }

    # ---------------------------------------------------------
    # Magic Methods
    # ---------------------------------------------------------

    def __contains__(
        self,
        pid: int,
    ) -> bool:

        return self.exists(pid)

    def __len__(
        self,
    ) -> int:

        return self.process_count

    def __iter__(self):

        return iter(
            self._cache,
        )

    def __repr__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}("
            f"processes={self.process_count}, "
            f"running={self.running_count})"
        )
