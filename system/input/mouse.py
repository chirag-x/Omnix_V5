"""
Omnix V5
Mouse Controller
"""

from __future__ import annotations

import logging
from pathlib import Path

import pyautogui

logger = logging.getLogger(__name__)

# Prevent exceptions when the mouse reaches a screen corner.
pyautogui.FAILSAFE = False


class Mouse:
    """
    Mouse controller.

    Provides:

        • Move
        • Click
        • Double Click
        • Right Click
        • Middle Click
        • Drag
        • Position
    """

    def __init__(self) -> None:

        self._enabled = True

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:

        return self._enabled

    def enable(self) -> None:

        self._enabled = True

    def disable(self) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Movement
    # ---------------------------------------------------------

    def move_to(
        self,
        x: int,
        y: int,
        *,
        duration: float = 0.0,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.moveTo(
            x,
            y,
            duration=duration,
        )

    def move_relative(
        self,
        dx: int,
        dy: int,
        *,
        duration: float = 0.0,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.moveRel(
            dx,
            dy,
            duration=duration,
        )

    def position(self) -> tuple[int, int]:

        return pyautogui.position()

    # ---------------------------------------------------------
    # Clicks
    # ---------------------------------------------------------

    def click(
        self,
        *,
        x: int | None = None,
        y: int | None = None,
        clicks: int = 1,
        interval: float = 0.0,
        button: str = "left",
    ) -> None:

        if not self._enabled:
            return

        pyautogui.click(
            x=x,
            y=y,
            clicks=clicks,
            interval=interval,
            button=button,
        )

    def double_click(
        self,
        *,
        x: int | None = None,
        y: int | None = None,
    ) -> None:

        self.click(
            x=x,
            y=y,
            clicks=2,
        )

    def right_click(
        self,
        *,
        x: int | None = None,
        y: int | None = None,
    ) -> None:

        self.click(
            x=x,
            y=y,
            button="right",
        )

    def middle_click(
        self,
        *,
        x: int | None = None,
        y: int | None = None,
    ) -> None:

        self.click(
            x=x,
            y=y,
            button="middle",
        )

    # ---------------------------------------------------------
    # Button Control
    # ---------------------------------------------------------

    def mouse_down(
        self,
        *,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
    ) -> None:

        if not self._enabled:
            return

        pyautogui.mouseDown(
            x=x,
            y=y,
            button=button,
        )

    def mouse_up(
        self,
        *,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
    ) -> None:

        if not self._enabled:
            return

        pyautogui.mouseUp(
            x=x,
            y=y,
            button=button,
        )

    # ---------------------------------------------------------
    # Drag
    # ---------------------------------------------------------

    def drag_to(
        self,
        x: int,
        y: int,
        *,
        duration: float = 0.0,
        button: str = "left",
    ) -> None:

        if not self._enabled:
            return

        pyautogui.dragTo(
            x,
            y,
            duration=duration,
            button=button,
        )

    def drag_relative(
        self,
        dx: int,
        dy: int,
        *,
        duration: float = 0.0,
        button: str = "left",
    ) -> None:

        if not self._enabled:
            return

        pyautogui.dragRel(
            dx,
            dy,
            duration=duration,
            button=button,
        )

    # ---------------------------------------------------------
    # Scrolling
    # ---------------------------------------------------------

    def scroll(
        self,
        clicks: int,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.scroll(clicks)

    def horizontal_scroll(
        self,
        clicks: int,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.hscroll(clicks)

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def size(
        self,
    ) -> tuple[int, int]:

        return pyautogui.size()

    def on_screen(
        self,
        x: int,
        y: int,
    ) -> bool:

        return pyautogui.onScreen(
            x,
            y,
        )

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
            "position": self.position(),
            "screen_size": self.size(),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "Mouse(" f"enabled={self._enabled})"
