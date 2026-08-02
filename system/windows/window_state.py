"""
Omnix V5
Window State Controller

Controls the state of desktop windows.
"""

from __future__ import annotations

import logging

import win32con
import win32gui

from system.models.window import Window

logger = logging.getLogger(__name__)


class WindowStateController:
    """
    Controls desktop window state.

    Responsibilities
    ----------------
    • Focus windows
    • Minimize windows
    • Maximize windows
    • Restore windows
    • Move windows
    • Resize windows
    • Close windows

    This class never searches for windows.
    """

    # ---------------------------------------------------------
    # Focus
    # ---------------------------------------------------------

    def focus(
        self,
        window: Window,
    ) -> bool:

        try:

            if window.minimized:
                self.restore(window)

            win32gui.SetForegroundWindow(
                window.handle,
            )

            window.focus()

            return True

        except Exception:

            logger.exception(
                "Failed to focus window %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Minimize
    # ---------------------------------------------------------

    def minimize(
        self,
        window: Window,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                window.handle,
                win32con.SW_MINIMIZE,
            )

            window.minimize()

            return True

        except Exception:

            logger.exception(
                "Failed to minimize %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Maximize
    # ---------------------------------------------------------

    def maximize(
        self,
        window: Window,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                window.handle,
                win32con.SW_MAXIMIZE,
            )

            window.maximize()

            return True

        except Exception:

            logger.exception(
                "Failed to maximize %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Restore
    # ---------------------------------------------------------

    def restore(
        self,
        window: Window,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                window.handle,
                win32con.SW_RESTORE,
            )

            window.restore()

            return True

        except Exception:

            logger.exception(
                "Failed to restore %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Move
    # ---------------------------------------------------------

    def move(
        self,
        window: Window,
        left: int,
        top: int,
    ) -> bool:

        try:

            win32gui.MoveWindow(
                window.handle,
                left,
                top,
                window.width,
                window.height,
                True,
            )

            window.move(
                left,
                top,
            )

            return True

        except Exception:

            logger.exception(
                "Failed to move %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Resize
    # ---------------------------------------------------------

    def resize(
        self,
        window: Window,
        width: int,
        height: int,
    ) -> bool:

        try:

            win32gui.MoveWindow(
                window.handle,
                window.left,
                window.top,
                width,
                height,
                True,
            )

            window.resize(
                width,
                height,
            )

            return True

        except Exception:

            logger.exception(
                "Failed to resize %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Move + Resize
    # ---------------------------------------------------------

    def set_geometry(
        self,
        window: Window,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> bool:

        try:

            win32gui.MoveWindow(
                window.handle,
                left,
                top,
                width,
                height,
                True,
            )

            window.update_geometry(
                left,
                top,
                width,
                height,
            )

            return True

        except Exception:

            logger.exception(
                "Failed updating geometry for %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Close
    # ---------------------------------------------------------

    def close(
        self,
        window: Window,
    ) -> bool:

        try:

            win32gui.PostMessage(
                window.handle,
                win32con.WM_CLOSE,
                0,
                0,
            )

            return True

        except Exception:

            logger.exception(
                "Failed closing %s",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Visibility
    # ---------------------------------------------------------

    def hide(
        self,
        window: Window,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                window.handle,
                win32con.SW_HIDE,
            )

            window.visible = False

            return True

        except Exception:

            logger.exception(
                "Failed hiding %s",
                window.title,
            )

            return False

    def show(
        self,
        window: Window,
    ) -> bool:

        try:

            win32gui.ShowWindow(
                window.handle,
                win32con.SW_SHOW,
            )

            window.visible = True

            return True

        except Exception:

            logger.exception(
                "Failed showing %s",
                window.title,
            )

            return False