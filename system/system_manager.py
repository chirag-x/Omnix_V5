"""
Omnix V5
System Manager

Central lifecycle manager for all Omnix subsystems.
"""

from __future__ import annotations

import logging

# Services

from .services.app_controller import AppController
from .services.process_controller import ProcessController
from .services.window_controller import WindowController
from .services.power_controller import PowerController
from .services.resource_controller import ResourceController

# Managers

from .applications.application_manager import ApplicationManager
from .processes.process_manager import ProcessManager
from .filesystem.file_manager import FileManager
from .windows.window_manager import WindowManager
from .input.input_manager import InputManager
from .ui.ui_manager import UIManager
from .power.power_manager import PowerManager

# Memory

from .memory.system_memory import SystemMemory

# Diagnostics

from .diagnostics.health_check import HealthCheck
from .diagnostics.performance import PerformanceMonitor
from .diagnostics.system_report import SystemReport

# Automation

from .automation.action_executor import ActionExecutor
from .automation.automation_manager import AutomationManager

logger = logging.getLogger(__name__)


class SystemManager:
    """
    Central controller for Omnix.

    Responsible for creating,
    connecting and managing
    all subsystems.
    """

    def __init__(
        self,
    ) -> None:

        self._initialized = False

        #
        # Services
        #

        self._app_controller = AppController()

        self._process_controller = ProcessController()

        self._window_controller = WindowController()

        self._power_controller = PowerController()

        self._resource_controller = ResourceController()

        #
        # Managers
        #

        self._applications = None

        self._processes = None

        self._filesystem = None

        self._windows = None

        self._input = None

        self._ui = None

        self._power = None

        self._memory = None

        #
        # Diagnostics
        #

        self._health = None

        self._performance = None

        self._report = None

        #
        # Automation
        #

        self._action_executor = None

        self._automation = None

    # ---------------------------------------------------------
    # Manager Creation
    # ---------------------------------------------------------

    def _create_managers(
        self,
    ) -> None:
        """
        Create and connect all managers.
        """

        #
        # Core Managers
        #

        self._applications = ApplicationManager(
            controller=self._app_controller,
        )

        self._processes = ProcessManager(
            controller=self._process_controller,
        )

        self._windows = WindowManager(
            controller=self._window_controller,
        )

        self._filesystem = FileManager()

        self._input = InputManager()

        self._ui = UIManager()

        #
        # Power
        #

        self._power = PowerManager(
            controller=self._power_controller,
        )

        #
        # Memory
        #

        self._memory = SystemMemory()

        #
        # Diagnostics
        #

        self._health = HealthCheck()

        self._performance = PerformanceMonitor(
            resource_controller=self._resource_controller,
        )

        self._report = SystemReport(
            self._health,
            self._performance,
        )
        #
        # Automation
        #

        self._action_executor = ActionExecutor(
            applications=self._applications,
            input_manager=self._input,
        )

        self._automation = AutomationManager(
            action_executor=self._action_executor,
        )

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    @property
    def initialized(
        self,
    ) -> bool:

        return self._initialized

    def start(
        self,
    ) -> None:
        """
        Start Omnix system.
        """

        if self._initialized:

            return

        logger.info("Starting Omnix system...")

        #
        # Create managers
        #

        self._create_managers()

        #
        # Initialize subsystems
        #

        managers = [
            self._applications,
            self._processes,
            self._filesystem,
            self._windows,
            self._input,
            self._ui,
            self._power,
            self._automation,
        ]

        for manager in managers:

            if manager is not None:

                initialize = getattr(
                    manager,
                    "initialize",
                    None,
                )

                if initialize:

                    initialize()

        self._initialized = True

        logger.info("Omnix system started.")

    def shutdown(
        self,
    ) -> None:
        """
        Shutdown Omnix safely.
        """

        if not self._initialized:

            return

        logger.info("Stopping Omnix system...")

        managers = [
            self._automation,
            self._ui,
            self._input,
            self._windows,
            self._filesystem,
            self._processes,
            self._applications,
        ]

        for manager in managers:

            if manager is not None:

                shutdown = getattr(
                    manager,
                    "shutdown",
                    None,
                )

                if shutdown:

                    shutdown()

        self._initialized = False

        logger.info("Omnix stopped.")

    # ---------------------------------------------------------
    # Accessors
    # ---------------------------------------------------------

    @property
    def applications(
        self,
    ) -> ApplicationManager:

        return self._applications

    @property
    def processes(
        self,
    ) -> ProcessManager:

        return self._processes

    @property
    def filesystem(
        self,
    ) -> FileManager:

        return self._filesystem

    @property
    def windows(
        self,
    ) -> WindowManager:

        return self._windows

    @property
    def input(
        self,
    ) -> InputManager:

        return self._input

    @property
    def ui(
        self,
    ) -> UIManager:

        return self._ui

    @property
    def power(
        self,
    ) -> PowerManager:

        return self._power

    @property
    def memory(
        self,
    ) -> SystemMemory:

        return self._memory

    @property
    def automation(
        self,
    ) -> AutomationManager:

        return self._automation

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:
        """
        Return complete system status.
        """

        return {
            "initialized": self._initialized,
            "applications": (
                self._applications.statistics() if self._applications else None
            ),
            "processes": (self._processes.statistics() if self._processes else None),
            "filesystem": (self._filesystem.statistics() if self._filesystem else None),
            "windows": (self._windows.statistics() if self._windows else None),
            "input": (self._input.statistics() if self._input else None),
            "ui": (self._ui.statistics() if self._ui else None),
            "power": (self._power.statistics() if self._power else None),
            "memory": (self._memory.statistics() if self._memory else None),
            "automation": (self._automation.statistics() if self._automation else None),
        }

    def __repr__(
        self,
    ) -> str:

        return "SystemManager(" f"initialized={self._initialized})"
