"""
Omnix V5
Keyboard Controller
"""

from __future__ import annotations

import logging

import pyautogui

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = False


class Keyboard:
    """
    Keyboard controller.

    Provides:

        • Press keys
        • Hold keys
        • Release keys
        • Key combinations
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
    # Basic Keys
    # ---------------------------------------------------------

    def press(
        self,
        key: str,
        *,
        presses: int = 1,
        interval: float = 0.0,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.press(
            key,
            presses=presses,
            interval=interval,
        )

    def key_down(
        self,
        key: str,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.keyDown(key)

    def key_up(
        self,
        key: str,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.keyUp(key)

    # ---------------------------------------------------------
    # Combinations
    # ---------------------------------------------------------

    def hotkey(
        self,
        *keys: str,
        interval: float = 0.0,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.hotkey(
            *keys,
            interval=interval,
        )

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    def hold(
        self,
        key: str,
    ):

        if not self._enabled:
            raise RuntimeError("Keyboard is disabled.")

        return pyautogui.hold(key)

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "Keyboard(" f"enabled={self._enabled})"
