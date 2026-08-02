"""
Omnix V5
UI Controller

Low-level UI interaction service.
"""

from __future__ import annotations

import logging

import pyautogui

logger = logging.getLogger(__name__)


class UIController:
    """
    Low-level UI automation controller.

    Responsible for direct interaction
    with the desktop UI.
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
    # Mouse Actions
    # ---------------------------------------------------------

    def click(
        self,
        x: int,
        y: int,
    ) -> bool:

        if not self._enabled:

            return False

        try:

            pyautogui.click(
                x,
                y,
            )

            return True

        except Exception as exc:

            logger.error(
                "UI click failed: %s",
                exc,
            )

            return False

    def double_click(
        self,
        x: int,
        y: int,
    ) -> bool:

        try:

            pyautogui.doubleClick(
                x,
                y,
            )

            return True

        except Exception:

            return False

    def move_cursor(
        self,
        x: int,
        y: int,
        duration: float = 0.0,
    ) -> bool:

        try:

            pyautogui.moveTo(
                x,
                y,
                duration=duration,
            )

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Keyboard
    # ---------------------------------------------------------

    def type_text(
        self,
        text: str,
    ) -> bool:

        try:

            pyautogui.write(
                text,
            )

            return True

        except Exception:

            return False

    def press_key(
        self,
        key: str,
    ) -> bool:

        try:

            pyautogui.press(
                key,
            )

            return True

        except Exception:

            return False

    def hotkey(
        self,
        *keys: str,
    ) -> bool:

        try:

            pyautogui.hotkey(
                *keys,
            )

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Screenshot
    # ---------------------------------------------------------

    def screenshot(
        self,
        path: str | None = None,
    ):

        try:

            image = pyautogui.screenshot()

            if path:

                image.save(
                    path,
                )

            return image

        except Exception as exc:

            logger.error(
                "Screenshot failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # Screen
    # ---------------------------------------------------------

    def screen_size(
        self,
    ) -> tuple[int, int]:

        return pyautogui.size()

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

        return "UIController(" f"enabled={self._enabled})"
