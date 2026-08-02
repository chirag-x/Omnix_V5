"""
Omnix V5
Application Registry

Reads installed applications from the Windows Registry.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict
import winreg

from system.models.application import Application

logger = logging.getLogger(__name__)


class ApplicationRegistry:
    """
    Reads installed applications from the Windows Registry.

    Responsibilities
    ----------------
    • Read HKLM uninstall entries
    • Read HKCU uninstall entries
    • Read 32-bit uninstall entries
    • Convert registry data into Application models
    • Maintain an in-memory cache

    This class DOES NOT:

    • Scan folders
    • Parse shortcuts
    • Launch applications
    • Detect running processes
    """

    # ---------------------------------------------------------
    # Registry locations
    # ---------------------------------------------------------

    REGISTRY_PATHS = (
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
    )

    # ---------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------

    def __init__(self) -> None:

        self._applications: Dict[str, Application] = {}

        self._last_scan: datetime | None = None

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    @property
    def last_scan(self) -> datetime | None:
        """Time of the most recent registry scan."""
        return self._last_scan

    @property
    def count(self) -> int:
        """Number of cached applications."""
        return len(self._applications)

    def load(self) -> dict[str, Application]:
        """
        Load all installed applications from the registry.

        Returns
        -------
        dict[str, Application]
        """

        logger.info("Loading installed applications from registry...")

        self._applications.clear()

        self._scan_registry()

        self._last_scan = datetime.now()

        logger.info(
            "Registry scan complete. %d applications discovered.",
            len(self._applications),
        )

        return self._applications

    def refresh(self) -> dict[str, Application]:
        """Reload registry data."""
        return self.load()

    def get_applications(self) -> list[Application]:
        """Return all cached applications."""
        return sorted(
            self._applications.values(),
            key=lambda app: app.name.lower(),
        )

    def get_application(self, name: str) -> Application | None:
        """Return a cached application by name."""

        return self._applications.get(name.lower())

    def clear(self) -> None:
        """Clear the internal cache."""

        self._applications.clear()

        self._last_scan = None

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _scan_registry(self):
        """
        Placeholder until application scanner is implemented.
        """

        return {}

    def _read_registry_key(
        self,
        root: int,
        path: str,
    ) -> None:
        """
        Read one uninstall registry key.

        Implemented in Part 2.
        """

        raise NotImplementedError

    def _parse_application(
        self,
        values: dict,
    ) -> Application | None:
        """
        Convert registry values into an Application model.

        Implemented in Part 3.
        """

        raise NotImplementedError

    def _add_application(
        self,
        application: Application,
    ) -> None:
        """
        Add an application to the cache.

        Duplicate handling is implemented in Part 3.
        """

        raise NotImplementedError
