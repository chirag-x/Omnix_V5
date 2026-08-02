"""
Omnix V5
Win32 Utilities

Windows API helper functions.
"""

from __future__ import annotations

import logging
import platform

logger = logging.getLogger(__name__)


class Win32Utils:
    """
    Windows API helper.
    """

    # ---------------------------------------------------------
    # Platform Check
    # ---------------------------------------------------------

    @staticmethod
    def is_windows() -> bool:
        """
        Check if running on Windows.
        """

        return platform.system() == "Windows"

    # ---------------------------------------------------------
    # Screen Size
    # ---------------------------------------------------------

    @staticmethod
    def screen_size() -> tuple[int, int]:
        """
        Get screen resolution.
        """

        try:

            import ctypes

            user32 = ctypes.windll.user32

            return (
                user32.GetSystemMetrics(0),
                user32.GetSystemMetrics(1),
            )

        except Exception as exc:

            logger.error(
                "Screen size failed: %s",
                exc,
            )

            return (
                0,
                0,
            )

    # ---------------------------------------------------------
    # Active Window Handle
    # ---------------------------------------------------------

    @staticmethod
    def active_window_handle():
        """
        Return active window handle.
        """

        try:

            import ctypes

            return ctypes.windll.user32.GetForegroundWindow()

        except Exception as exc:

            logger.error(
                "Active window failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # Send Message
    # ---------------------------------------------------------

    @staticmethod
    def send_message(
        hwnd,
        message,
        w_param=0,
        l_param=0,
    ) -> bool:
        """
        Send Windows message.
        """

        try:

            import ctypes

            ctypes.windll.user32.SendMessageW(
                hwnd,
                message,
                w_param,
                l_param,
            )

            return True

        except Exception as exc:

            logger.error(
                "Send message failed: %s",
                exc,
            )

            return False

    # ---------------------------------------------------------
    # System Information
    # ---------------------------------------------------------

    @staticmethod
    def system_info() -> dict:
        """
        Basic Windows information.
        """

        return {
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "windows": Win32Utils.is_windows(),
        }

    def __repr__(
        self,
    ) -> str:

        return "Win32Utils()"
