"""
Omnix V5
Keyboard Controller

Low-level keyboard OS operations.
"""

from __future__ import annotations

import logging

import pyautogui

logger = logging.getLogger(__name__)


class KeyboardController:
    """
    Direct keyboard input controller.
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
    # Keyboard Actions
    # ---------------------------------------------------------

    def press(
        self,
        key: str,
    ) -> bool:

        if not self._enabled:

            return False

        try:

            pyautogui.press(
                key,
            )

            return True

        except Exception as exc:

            logger.error(
                "Key press failed: %s",
                exc,
            )

            return False

    def key_down(
        self,
        key: str,
    ) -> bool:

        try:

            pyautogui.keyDown(
                key,
            )

            return True

        except Exception:

            return False

    def key_up(
        self,
        key: str,
    ) -> bool:

        try:

            pyautogui.keyUp(
                key,
            )

            return True

        except Exception:

            return False

    def write(
        self,
        text: str,
        interval: float = 0.0,
    ) -> bool:

        try:

            pyautogui.write(
                text,
                interval=interval,
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

        return "KeyboardController(" f"enabled={self._enabled})"
