"""
Omnix V5
Clipboard Controller
"""

from __future__ import annotations

import logging

import pyperclip

logger = logging.getLogger(__name__)


class Clipboard:
    """
    Clipboard controller.

    Provides:

        • Copy text
        • Read clipboard
        • Clear clipboard
        • Check contents
    """

    def __init__(self) -> None:

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

    def disable(
        self,
    ) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Clipboard
    # ---------------------------------------------------------

    def set_text(
        self,
        text: str,
    ) -> None:

        if not self._enabled:
            return

        pyperclip.copy(text)

    def get_text(
        self,
    ) -> str:

        if not self._enabled:
            return ""

        return pyperclip.paste()

    def clear(
        self,
    ) -> None:

        if not self._enabled:
            return

        pyperclip.copy("")

    def has_text(
        self,
    ) -> bool:

        return bool(self.get_text().strip())

    # ---------------------------------------------------------
    # Clipboard Snapshot
    # ---------------------------------------------------------

    def backup(
        self,
    ) -> str:
        """
        Returns the current clipboard contents.

        The caller is responsible for storing
        the returned value and passing it back
        to restore().
        """

        return self.get_text()

    def restore(
        self,
        text: str,
    ) -> None:

        self.set_text(text)

    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def append_text(
        self,
        text: str,
    ) -> None:

        if not self._enabled:
            return

        current = self.get_text()

        self.set_text(
            current + text,
        )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
            "has_text": self.has_text(),
            "length": len(
                self.get_text(),
            ),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "Clipboard(" f"enabled={self._enabled})"
