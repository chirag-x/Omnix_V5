"""
Omnix V5
Application Manager

Main entry point for the Applications subsystem.
"""

from __future__ import annotations

import logging
from threading import Lock

from system.models.application import Application

from .app_discovery import ApplicationDiscovery
from .application_cache import ApplicationCache
from .application_history import ApplicationHistory
from .application_monitor import ApplicationMonitor
from .installer_detector import InstallerDetector
from .launch_strategy import LaunchStrategy
from .process_resolver import ProcessResolver

logger = logging.getLogger(__name__)


class ApplicationManager:
    """
    Central manager for all application operations.

    Responsibilities
    ----------------
    • Application discovery
    • Application lookup
    • Launching
    • Running process resolution
    • Monitoring
    • Launch history
    • Cache management

    Other Omnix modules should ONLY communicate
    with this class.
    """

    # ---------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------

    def __init__(
        self,
        controller=None,
        discovery=None,
        launcher=None,
        resolver=None,
        cache=None,
        history=None,
        monitor=None,
        installer_detector=None,
    ):

        self._initialized = False

        self._lock = Lock()

        # Components

        self._controller = controller

        self._discovery = discovery or ApplicationDiscovery()

        self._launcher = launcher or LaunchStrategy()

        self._resolver = resolver or ProcessResolver()

        self._cache = cache or ApplicationCache()

        self._history = history or ApplicationHistory()

        self._monitor = monitor or ApplicationMonitor()

        self._installer_detector = installer_detector or InstallerDetector()

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def initialized(self) -> bool:
        """Whether the manager has been initialized."""
        return self._initialized

    @property
    def application_count(self) -> int:
        """Number of discovered applications."""
        return self._cache.count

    @property
    def running_count(self) -> int:
        """Number of running applications."""
        return self._monitor.running_count()

    @property
    def last_scan(self):
        """Timestamp of the last application discovery."""
        return self._cache.last_updated

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def initialize(self) -> None:
        """
        Initialize the Applications subsystem.
        """

        with self._lock:

            if self._initialized:
                return

            logger.info("Initializing Application Manager...")

            applications = self._discovery.discover()

            self._cache.update(applications)

            self._monitor.update(applications)

            self._initialized = True

            logger.info(
                "Application Manager initialized (%d applications).",
                self.application_count,
            )

    def shutdown(self) -> None:
        """
        Shutdown the Applications subsystem.
        """

        with self._lock:

            if not self._initialized:
                return

            logger.info("Shutting down Application Manager...")

            self._cache.clear()

            self._initialized = False

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _ensure_initialized(self) -> None:

        if not self._initialized:

            raise RuntimeError("ApplicationManager is not initialized.")

        # ---------------------------------------------------------

    # Discovery
    # ---------------------------------------------------------

    def refresh(self) -> list[Application]:
        """
        Refresh the application catalog.

        Returns
        -------
        list[Application]
            Updated list of discovered applications.
        """

        self._ensure_initialized()

        with self._lock:

            logger.info("Refreshing application catalog...")

            applications = self._discovery.discover()

            self._cache.update(applications)

            self._monitor.update(applications)

            logger.info(
                "Refresh complete (%d applications).",
                self.application_count,
            )

            return applications

    # ---------------------------------------------------------
    # Installed Applications
    # ---------------------------------------------------------

    def applications(self) -> list[Application]:
        """
        Return all installed applications.
        """

        self._ensure_initialized()

        return self._cache.all()

    def application_names(self) -> list[str]:
        """
        Return installed application names.
        """

        return [app.display_name for app in self.applications()]

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def find(
        self,
        name: str,
    ) -> Application | None:
        """
        Find an application by name.
        """

        self._ensure_initialized()

        if not name:
            return None

        return self._cache.get(name)

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        Check whether an application exists.
        """

        self._ensure_initialized()

        return self._cache.exists(name)

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        query: str,
    ) -> list[Application]:
        """
        Search installed applications.
        """

        self._ensure_initialized()

        return self._cache.search(query)

    # ---------------------------------------------------------
    # Running Applications
    # ---------------------------------------------------------

    def running_applications(
        self,
    ) -> list[Application]:
        """
        Return running applications.
        """

        self._ensure_initialized()

        return self._monitor.running()

    def is_running(
        self,
        name: str,
    ) -> bool:
        """
        Check whether an application is running.
        """

        self._ensure_initialized()

        application = self.find(name)

        if application is None:
            return False

        return self._monitor.is_running(application)

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(self) -> dict[str, int]:
        """
        Return application statistics.
        """

        self._ensure_initialized()

        return {
            "installed": self.application_count,
            "running": self.running_count,
            "cached": self._cache.count,
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def __contains__(
        self,
        name: str,
    ) -> bool:

        return self.exists(name)

    def __len__(self) -> int:

        return self.application_count

    def __iter__(self):

        return iter(self.applications())

        # ---------------------------------------------------------

    # Launching
    # ---------------------------------------------------------

    def launch(
        self,
        name: str,
        *arguments: str,
    ) -> bool:
        """
        Launch an application.

        Parameters
        ----------
        name:
            Application name.

        arguments:
            Optional launch arguments.
        """

        self._ensure_initialized()

        application = self.find(name)

        logger.info("=" * 60)
        logger.info("[ApplicationManager] Launch Request")
        logger.info(f"Requested name      : {name}")

        if application:
            logger.info(f"Display Name        : {application.display_name}")
            logger.info(f"Executable          : {application.executable}")
            logger.info(f"Launch Command      : {application.launch_command}")
            logger.info(f"Install Path        : {application.install_path}")
        else:
            logger.error("Application lookup returned None")

        logger.info("=" * 60)

        if application is None:

            logger.warning(
                "Application not found: %s",
                name,
            )

            return False

        logger.info("[ApplicationManager] Calling LaunchStrategy.launch()")
        success = self._launcher.launch(
            application,
            *arguments,
        )

        if success:

            self._history.record_launch(application)

            self._monitor.update(
                self.applications(),
            )

            logger.info(
                "Launched application: %s",
                application.display_name,
            )

        return success

    # ---------------------------------------------------------

    def launch_as_admin(
        self,
        name: str,
        *arguments: str,
    ) -> bool:
        """
        Launch an application as Administrator.
        """

        self._ensure_initialized()

        application = self.find(name)

        if application is None:
            return False

        executable = application.executable

        if not executable:
            return False

        success = self._launcher.launch_as_admin(
            executable,
            *arguments,
        )

        if success:

            self._history.record_launch(application)

        return success

    # ---------------------------------------------------------

    def launch_file(
        self,
        file: str,
    ) -> bool:
        """
        Open a file with its default application.
        """

        self._ensure_initialized()

        return self._launcher.launch_file(file)

    # ---------------------------------------------------------

    def launch_url(
        self,
        url: str,
    ) -> bool:
        """
        Open a URL or protocol.

        Examples
        --------
        https://google.com

        spotify:

        steam:

        mailto:
        """

        self._ensure_initialized()

        return self._launcher.launch_url(url)

    # ---------------------------------------------------------
    # History
    # ---------------------------------------------------------

    def history(self):

        self._ensure_initialized()

        return self._history.history()

    def recent_applications(
        self,
        limit: int = 10,
    ):

        self._ensure_initialized()

        return self._history.recent(limit)

    def most_used(
        self,
        limit: int = 10,
    ):

        self._ensure_initialized()

        return self._history.most_used(limit)

    # ---------------------------------------------------------
    # Callbacks
    # ---------------------------------------------------------

    def on_application_started(
        self,
        callback,
    ) -> None:

        self._monitor.on_application_started(
            callback,
        )

    def on_application_stopped(
        self,
        callback,
    ) -> None:

        self._monitor.on_application_stopped(
            callback,
        )

        # ---------------------------------------------------------

    # Background Monitoring
    # ---------------------------------------------------------

    def start_monitoring(self) -> None:
        """
        Start application monitoring.

        Currently performs an initial update.
        Future versions will start a background thread.
        """

        self._ensure_initialized()

        logger.info("Starting application monitoring...")

        self._monitor.update(
            self.applications(),
        )

    def stop_monitoring(self) -> None:
        """
        Stop application monitoring.

        Reserved for future threaded implementation.
        """

        self._ensure_initialized()

        logger.info("Stopping application monitoring...")

    def update_monitor(self) -> None:
        """
        Perform one monitoring update.
        """

        self._ensure_initialized()

        self._monitor.update(
            self.applications(),
        )

    # ---------------------------------------------------------
    # Cache
    # ---------------------------------------------------------

    def cache(self) -> ApplicationCache:
        """
        Return the application cache.
        """

        self._ensure_initialized()

        return self._cache

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def diagnostics(self) -> dict:
        """
        Return diagnostic information.
        """

        self._ensure_initialized()

        return {
            "initialized": self._initialized,
            "installed": self.application_count,
            "running": self.running_count,
            "last_scan": self.last_scan,
            "history": self._history.count,
        }

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    def export(self) -> list[dict]:
        """
        Export all applications.
        """

        self._ensure_initialized()

        exported = []

        for application in self.applications():

            exported.append(application.to_dict())

        return exported

    # ---------------------------------------------------------
    # Reload
    # ---------------------------------------------------------

    def reload(self) -> None:
        """
        Reload the complete subsystem.
        """

        self.shutdown()

        self.initialize()

    # ---------------------------------------------------------
    # Magic Methods
    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"{self.__class__.__name__}("
            f"applications={self.application_count}, "
            f"running={self.running_count})"
        )
