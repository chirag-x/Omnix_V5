"""
Omnix V5
Window Controller

Low-level OS window operations.
"""

from __future__ import annotations

import logging

import win32con
import win32gui

logger = logging.getLogger(__name__)


class WindowController:
    """
    Direct Windows API window controller.
    """

    def __init__(self) -> None:

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
    # Window Actions
    # ---------------------------------------------------------

    def focus(
        self,
        handle: int,
    ) -> bool:

        if not self._enabled:
            return False

        try:

            win32gui.SetForegroundWindow(
                handle,
            )

            return True

        except Exception as exc:

            logger.error(
                "Focus failed: %s",
                exc,
            )

            return False

    def minimize(
        self,
        handle: int,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                handle,
                win32con.SW_MINIMIZE,
            )

            return True

        except Exception:

            return False

    def maximize(
        self,
        handle: int,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                handle,
                win32con.SW_MAXIMIZE,
            )

            return True

        except Exception:

            return False

    def restore(
        self,
        handle: int,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                handle,
                win32con.SW_RESTORE,
            )

            return True

        except Exception:

            return False

    def hide(
        self,
        handle: int,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                handle,
                win32con.SW_HIDE,
            )

            return True

        except Exception:

            return False

    def show(
        self,
        handle: int,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                handle,
                win32con.SW_SHOW,
            )

            return True

        except Exception:

            return False

    def close(
        self,
        handle: int,
    ) -> bool:

        try:

            win32gui.PostMessage(
                handle,
                win32con.WM_CLOSE,
                0,
                0,
            )

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def move(
        self,
        handle: int,
        left: int,
        top: int,
    ) -> bool:

        try:

            rect = win32gui.GetWindowRect(
                handle,
            )

            width = rect[2] - rect[0]

            height = rect[3] - rect[1]

            win32gui.MoveWindow(
                handle,
                left,
                top,
                width,
                height,
                True,
            )

            return True

        except Exception:

            return False

    def resize(
        self,
        handle: int,
        width: int,
        height: int,
    ) -> bool:

        try:

            rect = win32gui.GetWindowRect(
                handle,
            )

            win32gui.MoveWindow(
                handle,
                rect[0],
                rect[1],
                width,
                height,
                True,
            )

            return True

        except Exception:

            return False

    def set_geometry(
        self,
        handle: int,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> bool:

        try:

            win32gui.MoveWindow(
                handle,
                left,
                top,
                width,
                height,
                True,
            )

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def exists(
        self,
        handle: int,
    ) -> bool:

        return win32gui.IsWindow(
            handle,
        )

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
        }

    def __repr__(
        self,
    ) -> str:

        return "WindowController(" f"enabled={self._enabled})"
