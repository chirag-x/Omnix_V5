"""
Omnix V5
Startup Manager

Manages Windows startup applications.
"""

from __future__ import annotations

import logging
import os
import subprocess
import winreg
from pathlib import Path

logger = logging.getLogger(__name__)


class StartupManager:
    """
    Manage Windows startup applications.

    Responsibilities
    ----------------
    • Read startup applications
    • Add startup entries
    • Remove startup entries
    • Read Startup folders
    """

    RUN_KEYS = (
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ),
    )

    def startup_folder(self) -> Path:
        """
        Current user's Startup folder.
        """

        return (
            Path(os.getenv("APPDATA"))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
        )

    # ---------------------------------------------------------
    # Registry
    # ---------------------------------------------------------

    def registry_entries(self) -> dict[str, str]:
        """
        Return startup registry entries.
        """

        entries = {}

        for hive, path in self.RUN_KEYS:

            try:

                key = winreg.OpenKey(
                    hive,
                    path,
                )

                count = winreg.QueryInfoKey(key)[1]

                for i in range(count):

                    name, value, _ = winreg.EnumValue(
                        key,
                        i,
                    )

                    entries[name] = value

            except OSError:

                continue

        return entries

    # ---------------------------------------------------------
    # Startup Folder
    # ---------------------------------------------------------

    def startup_items(self) -> list[Path]:
        """
        Return Startup folder items.
        """

        folder = self.startup_folder()

        if not folder.exists():

            return []

        return list(folder.iterdir())

    # ---------------------------------------------------------
    # Add
    # ---------------------------------------------------------

    def add(
        self,
        name: str,
        executable: str,
    ) -> bool:
        """
        Add registry startup entry.
        """

        try:

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )

            winreg.SetValueEx(
                key,
                name,
                0,
                winreg.REG_SZ,
                executable,
            )

            winreg.CloseKey(key)

            return True

        except Exception:

            logger.exception(
                "Unable to add startup entry."
            )

            return False

    # ---------------------------------------------------------
    # Remove
    # ---------------------------------------------------------

    def remove(
        self,
        name: str,
    ) -> bool:
        """
        Remove startup entry.
        """

        try:

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )

            winreg.DeleteValue(
                key,
                name,
            )

            winreg.CloseKey(key)

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Launch
    # ---------------------------------------------------------

    def launch(
        self,
        executable: str,
    ) -> bool:
        """
        Launch a startup application immediately.
        """

        try:

            subprocess.Popen(
                executable,
                shell=True,
            )

            return True

        except Exception:

            logger.exception(
                "Unable to launch startup application."
            )

            return False

    # ---------------------------------------------------------
    # Queries
    # ---------------------------------------------------------

    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self.registry_entries()

    def count(self) -> int:

        return len(
            self.registry_entries()
        )

    def statistics(self) -> dict:

        return {
            "registry_entries": self.count(),
            "startup_folder_items": len(
                self.startup_items()
            ),
        }

    # ---------------------------------------------------------
    # Magic Methods
    # ---------------------------------------------------------

    def __len__(self):

        return self.count()

    def __repr__(self):

        return (
            f"{self.__class__.__name__}("
            f"entries={self.count()})"
        )