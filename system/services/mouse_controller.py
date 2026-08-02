"""
Omnix V5
Mouse Controller

Low-level mouse OS operations.
"""

from __future__ import annotations

import logging

import pyautogui

logger = logging.getLogger(__name__)


class MouseController:
    """
    Direct mouse input controller.
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
    # Movement
    # ---------------------------------------------------------

    def move(
        self,
        x: int,
        y: int,
        duration: float = 0.0,
    ) -> bool:

        if not self._enabled:

            return False

        try:

            pyautogui.moveTo(
                x,
                y,
                duration=duration,
            )

            return True

        except Exception as exc:

            logger.error(
                "Mouse move failed: %s",
                exc,
            )

            return False

    def position(
        self,
    ) -> tuple[int, int]:

        return pyautogui.position()

    # ---------------------------------------------------------
    # Buttons
    # ---------------------------------------------------------

    def click(
        self,
        button: str = "left",
    ) -> bool:

        try:

            pyautogui.click(
                button=button,
            )

            return True

        except Exception:

            return False

    def double_click(
        self,
        button: str = "left",
    ) -> bool:

        try:

            pyautogui.doubleClick(
                button=button,
            )

            return True

        except Exception:

            return False

    def mouse_down(
        self,
        button: str = "left",
    ) -> bool:

        try:

            pyautogui.mouseDown(
                button=button,
            )

            return True

        except Exception:

            return False

    def mouse_up(
        self,
        button: str = "left",
    ) -> bool:

        try:

            pyautogui.mouseUp(
                button=button,
            )

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Drag
    # ---------------------------------------------------------

    def drag(
        self,
        x: int,
        y: int,
        duration: float = 0.2,
        button: str = "left",
    ) -> bool:

        try:

            pyautogui.dragTo(
                x,
                y,
                duration=duration,
                button=button,
            )

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Scroll
    # ---------------------------------------------------------

    def scroll(
        self,
        amount: int,
    ) -> bool:

        try:

            pyautogui.scroll(
                amount,
            )

            return True

        except Exception:

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

        return "MouseController(" f"enabled={self._enabled})"
