"""
Omnix V5
PowerShell Utility

Safe PowerShell execution helper.
"""

from __future__ import annotations

import subprocess

import logging

logger = logging.getLogger(__name__)


class PowerShellManager:
    """
    Executes PowerShell commands.
    """

    def __init__(
        self,
        timeout: int = 30,
    ) -> None:

        self._timeout = timeout

    # ---------------------------------------------------------
    # Execute
    # ---------------------------------------------------------

    def execute(
        self,
        command: str,
    ) -> dict:
        """
        Execute PowerShell command.
        """

        try:

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "code": result.returncode,
            }

        except subprocess.TimeoutExpired:

            return {
                "success": False,
                "output": "",
                "error": "Command timed out",
                "code": -1,
            }

        except Exception as exc:

            logger.error(
                "PowerShell failed: %s",
                exc,
            )

            return {
                "success": False,
                "output": "",
                "error": str(exc),
                "code": -1,
            }

    # ---------------------------------------------------------
    # Simple Command
    # ---------------------------------------------------------

    def run(
        self,
        command: str,
    ) -> str | None:
        """
        Return only output.
        """

        result = self.execute(
            command,
        )

        if result["success"]:

            return result["output"]

        return None

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "timeout": self._timeout,
        }

    def __repr__(
        self,
    ) -> str:

        return "PowerShellManager(" f"timeout={self._timeout})"
