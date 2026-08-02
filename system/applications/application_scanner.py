"""
Omnix V5
Application Scanner

Scans directories for executable applications.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from system.models.application import Application

logger = logging.getLogger(__name__)


class ApplicationScanner:
    """
    Scans directories for executable applications.
    """

    DEFAULT_SCAN_PATHS = (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    )

    EXCLUDED_DIRECTORIES = {
        "Windows",
        "$Recycle.Bin",
        "System Volume Information",
        "Temp",
        "__pycache__",
    }

    def __init__(self) -> None:

        self._applications: dict[str, Application] = {}

        self._scan_paths: list[Path] = list(self.DEFAULT_SCAN_PATHS)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def add_scan_path(self, path: str | Path) -> None:
        """Add a custom scan directory."""

        path = Path(path)

        if path.exists() and path not in self._scan_paths:
            self._scan_paths.append(path)

    def remove_scan_path(self, path: str | Path) -> None:
        """Remove a scan directory."""

        path = Path(path)

        if path in self._scan_paths:
            self._scan_paths.remove(path)

    def scan(self) -> list[Application]:
        """
        Scan all configured directories.
        """

        logger.info("Scanning applications...")

        self._applications.clear()

        for directory in self._scan_paths:

            self._scan_directory(directory)

        logger.info(
            "Scanner discovered %d applications.",
            len(self._applications),
        )

        return list(self._applications.values())

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _scan_directory(self, directory: Path) -> None:

        if not directory.exists():
            return

        logger.info("Scanning: %s", directory)

        try:

            for root, dirs, files in os.walk(directory):

                # Skip unwanted folders
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in self.EXCLUDED_DIRECTORIES
                ]

                for filename in files:

                    if not filename.lower().endswith(".exe"):
                        continue

                    executable = Path(root) / filename

                    self._register_application(executable)

        except Exception:

            logger.exception(
                "Failed scanning %s",
                directory,
            )

    def _register_application(
        self,
        executable: Path,
    ) -> None:

        name = executable.stem.lower()

        if name in self._applications:
            return

        app = Application(
            name=name,
            display_name=executable.stem,
            executable=str(executable),
            install_path=str(executable.parent),
        )

        self._applications[name] = app