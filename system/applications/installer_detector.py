"""
Omnix V5
Installer Detector

Detects installer and uninstaller executables.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class InstallerDetector:
    """
    Detects installer and uninstaller executables.
    """

    INSTALLER_NAMES = {
        "setup",
        "install",
        "installer",
        "bootstrapper",
    }

    INSTALLER_KEYWORDS = (
        "setup",
        "install",
        "installer",
        "bootstrapper",
        "update",
        "updater",
        "redistributable",
        "redist",
        "runtime",
        "vc_redist",
        "directx",
        "dotnet",
    )

    UNINSTALLER_KEYWORDS = (
        "uninstall",
        "unins",
        "remove",
    )

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def is_installer(
        self,
        executable: str | Path,
    ) -> bool:
        """
        Returns True if the executable appears
        to be an installer.
        """

        executable = Path(executable)

        name = executable.stem.lower()

        if name in self.INSTALLER_NAMES:
            return True

        return any(
            keyword in name
            for keyword in self.INSTALLER_KEYWORDS
        )

    def is_uninstaller(
        self,
        executable: str | Path,
    ) -> bool:
        """
        Returns True if the executable appears
        to be an uninstaller.
        """

        executable = Path(executable)

        name = executable.stem.lower()

        return any(
            keyword in name
            for keyword in self.UNINSTALLER_KEYWORDS
        )

    def is_application(
        self,
        executable: str | Path,
    ) -> bool:
        """
        Returns True if the executable appears
        to be a normal application.
        """

        return (
            not self.is_installer(executable)
            and not self.is_uninstaller(executable)
        )