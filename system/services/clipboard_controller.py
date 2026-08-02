"""
Omnix V5
Clipboard Controller

Low-level clipboard OS operations.
"""

from __future__ import annotations

import logging

import pyperclip

logger = logging.getLogger(__name__)


class ClipboardController:
    """
    Direct clipboard access controller.
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
    # Clipboard Operations
    # ---------------------------------------------------------

    def get_text(
        self,
    ) -> str:
        """
        Read clipboard text.
        """

        if not self._enabled:

            return ""

        try:

            return pyperclip.paste()

        except Exception as exc:

            logger.error(
                "Clipboard read failed: %s",
                exc,
            )

            return ""

    def set_text(
        self,
        text: str,
    ) -> bool:
        """
        Write text to clipboard.
        """

        if not self._enabled:

            return False

        try:

            pyperclip.copy(
                text,
            )

            return True

        except Exception as exc:

            logger.error(
                "Clipboard write failed: %s",
                exc,
            )

            return False

    def clear(
        self,
    ) -> bool:
        """
        Clear clipboard content.
        """

        return self.set_text(
            "",
        )

    def has_text(
        self,
    ) -> bool:
        """
        Check whether clipboard contains text.
        """

        return bool(
            self.get_text(),
        )

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

        return "ClipboardController(" f"enabled={self._enabled})"
