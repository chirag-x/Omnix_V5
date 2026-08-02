"""
Omnix V5
Registry Utility

Windows Registry helper.
"""

from __future__ import annotations

import winreg

import logging

logger = logging.getLogger(__name__)


class RegistryManager:
    """
    Handles Windows Registry operations.
    """

    # ---------------------------------------------------------
    # Root Mapping
    # ---------------------------------------------------------

    ROOTS = {
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
        "HKCR": winreg.HKEY_CLASSES_ROOT,
    }

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    def read(
        self,
        root: str,
        path: str,
        name: str,
    ):
        """
        Read registry value.
        """

        try:

            key = winreg.OpenKey(
                self.ROOTS[root],
                path,
            )

            value, _ = winreg.QueryValueEx(
                key,
                name,
            )

            winreg.CloseKey(
                key,
            )

            return value

        except Exception as exc:

            logger.error(
                "Registry read failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------

    def write(
        self,
        root: str,
        path: str,
        name: str,
        value,
        value_type=winreg.REG_SZ,
    ) -> bool:
        """
        Write registry value.
        """

        try:

            key = winreg.CreateKey(
                self.ROOTS[root],
                path,
            )

            winreg.SetValueEx(
                key,
                name,
                0,
                value_type,
                value,
            )

            winreg.CloseKey(
                key,
            )

            return True

        except Exception as exc:

            logger.error(
                "Registry write failed: %s",
                exc,
            )

            return False

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete(
        self,
        root: str,
        path: str,
        name: str,
    ) -> bool:
        """
        Delete registry value.
        """

        try:

            key = winreg.OpenKey(
                self.ROOTS[root],
                path,
                0,
                winreg.KEY_SET_VALUE,
            )

            winreg.DeleteValue(
                key,
                name,
            )

            winreg.CloseKey(
                key,
            )

            return True

        except Exception as exc:

            logger.error(
                "Registry delete failed: %s",
                exc,
            )

            return False

    # ---------------------------------------------------------
    # Exists
    # ---------------------------------------------------------

    def exists(
        self,
        root: str,
        path: str,
        name: str,
    ) -> bool:
        """
        Check registry value.
        """

        return (
            self.read(
                root,
                path,
                name,
            )
            is not None
        )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "supported_roots": list(self.ROOTS.keys()),
        }

    def __repr__(
        self,
    ) -> str:

        return "RegistryManager()"
