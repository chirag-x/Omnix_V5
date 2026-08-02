"""
Omnix V5
Application Discovery

Combines all application discovery sources into a single catalog.
"""

from __future__ import annotations

import logging

from system.models.application import Application

from .application_registry import ApplicationRegistry
from .application_scanner import ApplicationScanner
from .shortcut_resolver import ShortcutResolver

logger = logging.getLogger(__name__)


class ApplicationDiscovery:
    """
    Discovers applications from multiple sources.

    Sources:
        • Windows Registry
        • Start Menu shortcuts
        • Desktop shortcuts
        • Executable scanning
    """

    def __init__(self) -> None:

        self._registry = ApplicationRegistry()

        self._scanner = ApplicationScanner()

        self._shortcuts = ShortcutResolver()

        self._applications: dict[str, Application] = {}

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def discover(self) -> list[Application]:
        """
        Discover applications from all available sources.
        """

        logger.info("Starting application discovery...")

        self._applications.clear()

        self._load_registry()

        self._load_shortcuts()

        self._load_scanner()

        logger.info(
            "Discovery complete. %d applications found.",
            len(self._applications),
        )

        return self.get_applications()

    def get_applications(self) -> list[Application]:

        return sorted(
            self._applications.values(),
            key=lambda app: app.display_name.lower(),
        )

    def get_application(
        self,
        name: str,
    ) -> Application | None:

        return self._applications.get(name.lower())

    # ---------------------------------------------------------
    # Registry
    # ---------------------------------------------------------

    def _load_registry(self) -> None:

        for app in self._registry.load().values():

            self._add(app)

    # ---------------------------------------------------------
    # Shortcuts
    # ---------------------------------------------------------

    def _load_shortcuts(self) -> None:

        shortcuts = []

        shortcuts.extend(
            self._shortcuts.resolve_start_menu()
        )

        shortcuts.extend(
            self._shortcuts.resolve_desktop()
        )

        for shortcut in shortcuts:

            target = shortcut.get("target")

            if target is None:
                continue

            app = Application(
                name=shortcut["name"].lower(),
                display_name=shortcut["name"],
                executable=str(target),
                install_path=str(target.parent),
                icon_path=shortcut.get("icon", ""),
            )

            self._add(app)

    # ---------------------------------------------------------
    # Scanner
    # ---------------------------------------------------------

    def _load_scanner(self) -> None:

        for app in self._scanner.scan():

            self._add(app)

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _add(
        self,
        application: Application,
    ) -> None:
        """
        Adds an application if it doesn't already exist.

        Registry entries always have priority over
        scanner and shortcut results.
        """

        key = application.name.lower()

        if key in self._applications:
            return

        self._applications[key] = application