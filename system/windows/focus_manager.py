"""
Omnix V5
Focus Manager

Manages the foreground desktop window.
"""

from __future__ import annotations

import logging
import time

import win32gui

from system.models.window import Window

logger = logging.getLogger(__name__)


class FocusManager:
    """
    Manages desktop focus.

    Responsibilities
    ----------------
    • Get focused window
    • Check focus
    • Wait for focus
    • Focus window
    """

    def __init__(self) -> None:
        pass

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def foreground_handle(self) -> int | None:
        """
        Returns the current foreground window handle.
        """

        try:
            return win32gui.GetForegroundWindow()

        except Exception:

            logger.exception(
                "Failed reading foreground window."
            )

            return None

    def is_focused(
        self,
        window: Window,
    ) -> bool:

        return (
            window.handle
            == self.foreground_handle()
        )

    # ---------------------------------------------------------
    # Focus
    # ---------------------------------------------------------

    def focus(
        self,
        window: Window,
    ) -> bool:
        """
        Brings a window to the foreground.
        """

        try:

            win32gui.SetForegroundWindow(
                window.handle,
            )

            return True

        except Exception:

            logger.exception(
                "Unable to focus '%s'",
                window.title,
            )

            return False

    # ---------------------------------------------------------
    # Wait
    # ---------------------------------------------------------

    def wait_for_focus(
        self,
        window: Window,
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> bool:
        """
        Wait until the given window becomes focused.
        """

        start = time.time()

        while (
            time.time() - start
        ) < timeout:

            if self.is_focused(
                window,
            ):
                return True

            time.sleep(
                interval,
            )

        return False

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def has_foreground(self) -> bool:

        return (
            self.foreground_handle()
            is not None
        )

    def __repr__(self) -> str:

        return "FocusManager()"