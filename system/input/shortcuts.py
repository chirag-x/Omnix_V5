"""
Omnix V5
Shortcut Controller
"""

from __future__ import annotations

import logging

from .hotkeys import Hotkeys
from .typing import Typing

logger = logging.getLogger(__name__)


class Shortcuts:
    """
    High-level keyboard workflows.
    """

    def __init__(self) -> None:

        self._hotkeys = Hotkeys()

        self._typing = Typing()

        self._enabled = True

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:

        return self._enabled

    def enable(self) -> None:

        self._enabled = True

        self._hotkeys.enable()

        self._typing.enable()

    def disable(self) -> None:

        self._enabled = False

        self._hotkeys.disable()

        self._typing.disable()

    # ---------------------------------------------------------
    # Common Workflows
    # ---------------------------------------------------------

    def select_and_copy(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.select_all()

        self._hotkeys.copy()

    def select_and_cut(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.select_all()

        self._hotkeys.cut()

    def paste_text(
        self,
        text: str,
    ) -> None:

        if not self._enabled:
            return

        self._typing.paste_text(
            text,
        )

    def replace_all(
        self,
        text: str,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.select_all()

        self._typing.paste_text(
            text,
        )

    # ---------------------------------------------------------
    # File Workflows
    # ---------------------------------------------------------

    def save_and_close(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.save()

        self._hotkeys.close_window()

    def save_and_refresh(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.save()

        self._hotkeys.refresh()

    # ---------------------------------------------------------
    # Window Workflows
    # ---------------------------------------------------------

    def minimize_all(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.show_desktop()

    def open_file_explorer(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.file_explorer()

    def open_settings(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.settings()

    def open_task_manager(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.task_manager()

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def next_window(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.switch_window()

    def lock_workstation(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._hotkeys.lock_screen()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def hotkeys(
        self,
    ) -> Hotkeys:

        return self._hotkeys

    @property
    def typing(
        self,
    ) -> Typing:

        return self._typing

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

        return "Shortcuts(" f"enabled={self._enabled})"
