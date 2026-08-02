"""
Omnix V5
Hotkey Controller
"""

from __future__ import annotations

import logging

from .keyboard import Keyboard

logger = logging.getLogger(__name__)


class Hotkeys:
    """
    System hotkeys.

    Provides common operating-system
    and application shortcuts.
    """

    def __init__(
        self,
    ) -> None:

        self._keyboard = Keyboard()

        self._enabled = True

    # ---------------------------------------------------------
    # Properties
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

        self._keyboard.enable()

    def disable(
        self,
    ) -> None:

        self._enabled = False

        self._keyboard.disable()

    # ---------------------------------------------------------
    # Clipboard
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

    def paste(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "v",
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

    def select_all(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "a",
        )

    # ---------------------------------------------------------
    # File
    # ---------------------------------------------------------

    def save(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "s",
        )

    def save_as(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "shift",
            "s",
        )

    def open(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "o",
        )

    def new(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "n",
        )

    # ---------------------------------------------------------
    # Window
    # ---------------------------------------------------------

    def switch_window(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "alt",
            "tab",
        )

    def close_window(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "alt",
            "f4",
        )

    def show_desktop(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "win",
            "d",
        )

    def lock_screen(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "win",
            "l",
        )

    # ---------------------------------------------------------
    # System
    # ---------------------------------------------------------

    def task_manager(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "shift",
            "esc",
        )

    def run_dialog(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "win",
            "r",
        )

    def file_explorer(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "win",
            "e",
        )

    def settings(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "win",
            "i",
        )

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def refresh(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.press(
            "f5",
        )

    def refresh_hard(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._keyboard.hotkey(
            "ctrl",
            "f5",
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

        return "Hotkeys(" f"enabled={self._enabled})"
