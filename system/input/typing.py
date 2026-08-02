"""
Omnix V5
Typing Controller
"""

from __future__ import annotations

import logging

import pyautogui
import pyperclip

from .keyboard import Keyboard

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = False


class Typing:
    """
    Text typing controller.

    Provides:

        • Type text
        • Paste text
        • Select all
        • Clear selection
        • Copy
        • Cut
        • Undo
        • Redo
    """

    def __init__(self) -> None:

        self._keyboard = Keyboard()

        self._enabled = True

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:

        return self._enabled

    def enable(self) -> None:

        self._enabled = True

        self._keyboard.enable()

    def disable(self) -> None:

        self._enabled = False

        self._keyboard.disable()

    # ---------------------------------------------------------
    # Typing
    # ---------------------------------------------------------

    def type_text(
        self,
        text: str,
        *,
        interval: float = 0.0,
    ) -> None:

        if not self._enabled:
            return

        pyautogui.write(
            text,
            interval=interval,
        )

    def paste_text(
        self,
        text: str,
    ) -> None:

        if not self._enabled:
            return

        previous = pyperclip.paste()

        try:

            pyperclip.copy(text)

            self._keyboard.hotkey(
                "ctrl",
                "v",
            )

        finally:

            pyperclip.copy(previous)

    # ---------------------------------------------------------
    # Selection
    # ---------------------------------------------------------

    def select_all(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "a",
        )

    def clear_selection(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.press(
            "backspace",
        )

    # ---------------------------------------------------------
    # Clipboard Actions
    # ---------------------------------------------------------

    def copy(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "c",
        )

    def cut(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "x",
        )

    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def undo(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "z",
        )

    def redo(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "y",
        )

    def delete(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.press(
            "delete",
        )

    def backspace(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.press(
            "backspace",
        )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def keyboard(
        self,
    ) -> Keyboard:

        return self._keyboard

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

        return "Typing(" f"enabled={self._enabled})"
