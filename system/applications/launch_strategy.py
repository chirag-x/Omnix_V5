"""
Omnix V5
Launch Strategy

Provides different strategies for launching applications.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from system.models.application import Application

logger = logging.getLogger(__name__)


class LaunchStrategy:
    """
    Handles launching applications using the appropriate strategy.
    """

    def launch(
        self,
        application: Application,
        *arguments: str,
    ) -> bool:
        """
        Launch an application.

        Returns
        -------
        bool
            True if launch request was successful.
        """

        if application.executable:

            executable = Path(application.executable)

            if executable.exists():
                return self._launch_executable(
                    executable,
                    *arguments,
                )

        if application.launch_command:
            return self._launch_command(
                application.launch_command,
                *arguments,
            )

        logger.warning(
            "Unable to launch '%s'. No executable or launch command.",
            application.display_name,
        )

        return False

    # ---------------------------------------------------------
    # Executables
    # ---------------------------------------------------------

    def _launch_executable(
        self,
        executable: Path,
        *arguments: str,
    ) -> bool:

        try:

            subprocess.Popen(
                [str(executable), *arguments],
                cwd=executable.parent,
            )

            logger.info("Launched %s", executable)

            return True

        except Exception:

            logger.exception(
                "Failed launching executable: %s",
                executable,
            )

            return False

    # ---------------------------------------------------------
    # Commands
    # ---------------------------------------------------------

    def _launch_command(
        self,
        command: str,
        *arguments: str,
    ) -> bool:

        try:

            subprocess.Popen(
                [command, *arguments],
                shell=True,
            )

            logger.info("Executed command: %s", command)

            return True

        except Exception:

            logger.exception(
                "Failed launching command: %s",
                command,
            )

            return False

    # ---------------------------------------------------------
    # URLs
    # ---------------------------------------------------------

    def launch_url(
        self,
        url: str,
    ) -> bool:

        try:

            parsed = urlparse(url)

            if not parsed.scheme:
                return False

            os.startfile(url)

            logger.info("Opened URL: %s", url)

            return True

        except Exception:

            logger.exception(
                "Failed opening URL: %s",
                url,
            )

            return False

    # ---------------------------------------------------------
    # Documents
    # ---------------------------------------------------------

    def launch_file(
        self,
        file: str | Path,
    ) -> bool:

        try:

            os.startfile(str(file))

            logger.info("Opened file: %s", file)

            return True

        except Exception:

            logger.exception(
                "Failed opening file: %s",
                file,
            )

            return False

    # ---------------------------------------------------------
    # Admin
    # ---------------------------------------------------------

    def launch_as_admin(
        self,
        executable: str | Path,
        *arguments: str,
    ) -> bool:

        try:

            import ctypes

            executable = str(executable)

            params = " ".join(arguments)

            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                executable,
                params,
                None,
                1,
            )

            return result > 32

        except Exception:

            logger.exception(
                "Failed launching as administrator."
            )

            return False