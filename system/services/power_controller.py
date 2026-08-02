"""
Omnix V5
Power Controller

Low-level Windows power operations.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class PowerController:
    """
    Direct Windows power control service.
    """

    def __init__(
        self,
    ) -> None:

        self._enabled = True

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def enabled(
        self,
    ) -> bool:

        return self._enabled


    def enable(
        self,
    ) -> None:

        self._enabled = True


    def disable(
        self,
    ) -> None:

        self._enabled = False


    # ---------------------------------------------------------
    # Power Actions
    # ---------------------------------------------------------

    def shutdown(
        self,
        force: bool = False,
    ) -> bool:
        """
        Shutdown the system.
        """

        return self._execute(
            "shutdown /s /t 0"
            + (" /f" if force else "")
        )


    def restart(
        self,
        force: bool = False,
    ) -> bool:
        """
        Restart the system.
        """

        return self._execute(
            "shutdown /r /t 0"
            + (" /f" if force else "")
        )


    def sleep(
        self,
    ) -> bool:
        """
        Put system into sleep mode.
        """

        try:

            os.system(
                "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
            )

            return True

        except Exception as exc:

            logger.error(
                "Sleep failed: %s",
                exc,
            )

            return False


    def hibernate(
        self,
    ) -> bool:
        """
        Hibernate the system.
        """

        return self._execute(
            "shutdown /h"
        )


    def lock(
        self,
    ) -> bool:
        """
        Lock workstation.
        """

        return self._execute(
            "rundll32.exe user32.dll,LockWorkStation"
        )


    def logoff(
        self,
    ) -> bool:
        """
        Log off current user.
        """

        return self._execute(
            "shutdown /l"
        )


    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _execute(
        self,
        command: str,
    ) -> bool:

        if not self._enabled:

            return False

        try:

            os.system(
                command,
            )

            logger.info(
                "Power command executed: %s",
                command,
            )

            return True

        except Exception as exc:

            logger.error(
                "Power command failed: %s",
                exc,
            )

            return False


    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
        }


    def __repr__(
        self,
    ) -> str:

        return (
            "PowerController("
            f"enabled={self._enabled})"
        )