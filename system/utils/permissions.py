"""
Omnix V5
Permissions Utility

Permission checking helpers.
"""

from __future__ import annotations

import os

from pathlib import Path


class PermissionManager:
    """
    Handles permission checks.
    """

    # ---------------------------------------------------------
    # Administrator Check
    # ---------------------------------------------------------

    @staticmethod
    def is_admin() -> bool:
        """
        Check if running as administrator.
        """

        try:

            import ctypes

            return bool(ctypes.windll.shell32.IsUserAnAdmin())

        except Exception:

            return False

    # ---------------------------------------------------------
    # Read Permission
    # ---------------------------------------------------------

    @staticmethod
    def can_read(
        path: str | Path,
    ) -> bool:
        """
        Check read permission.
        """

        try:

            return os.access(
                path,
                os.R_OK,
            )

        except Exception:

            return False

    # ---------------------------------------------------------
    # Write Permission
    # ---------------------------------------------------------

    @staticmethod
    def can_write(
        path: str | Path,
    ) -> bool:
        """
        Check write permission.
        """

        try:

            return os.access(
                path,
                os.W_OK,
            )

        except Exception:

            return False

    # ---------------------------------------------------------
    # Execute Permission
    # ---------------------------------------------------------

    @staticmethod
    def can_execute(
        path: str | Path,
    ) -> bool:
        """
        Check execute permission.
        """

        try:

            return os.access(
                path,
                os.X_OK,
            )

        except Exception:

            return False

    # ---------------------------------------------------------
    # Full Check
    # ---------------------------------------------------------

    @staticmethod
    def check(
        path: str | Path,
    ) -> dict:
        """
        Return permission status.
        """

        return {
            "exists": Path(path).exists(),
            "read": PermissionManager.can_read(path),
            "write": PermissionManager.can_write(path),
            "execute": PermissionManager.can_execute(path),
            "admin": PermissionManager.is_admin(),
        }

    def __repr__(
        self,
    ) -> str:

        return "PermissionManager()"
