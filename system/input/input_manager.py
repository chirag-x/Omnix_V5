"""
Omnix V5
Input Manager

Public API for the input subsystem.
"""

from __future__ import annotations

import logging

from .clipboard import Clipboard
from .gestures import Gestures
from .hotkeys import Hotkeys
from .keyboard import Keyboard
from .mouse import Mouse
from .scrolling import Scrolling
from .shortcuts import Shortcuts
from .typing import Typing

logger = logging.getLogger(__name__)


class InputManager:
    """
    Public interface for all input operations.

    Coordinates:

        • Mouse
        • Keyboard
        • Typing
        • Hotkeys
        • Scrolling
        • Clipboard
        • Gestures
        • Shortcuts
    """

    def __init__(
        self,
        mouse=None,
        keyboard=None,
        typing=None,
        hotkeys=None,
        scrolling=None,
        clipboard=None,
        gestures=None,
        shortcuts=None,
    ):

        self._mouse = mouse or Mouse()
        self._keyboard = keyboard or Keyboard()
        self._typing = typing or Typing()

        self._hotkeys = hotkeys or Hotkeys()

        self._scrolling = scrolling or Scrolling()

        self._clipboard = clipboard or Clipboard()

        self._gestures = gestures or Gestures()

        self._shortcuts = shortcuts or Shortcuts()

        self._initialized = False

    # ---------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------

    @property
    def initialized(self) -> bool:

        return self._initialized

    def initialize(self) -> None:

        if self._initialized:

            return

        logger.info("Initializing InputManager...")

        self._initialized = True

        logger.info("InputManager initialized.")

    def shutdown(self) -> None:

        logger.info("Shutting down InputManager...")

        self._initialized = False

    # ---------------------------------------------------------
    # Services
    # ---------------------------------------------------------

    @property
    def mouse(self) -> Mouse:

        return self._mouse

    @property
    def keyboard(self) -> Keyboard:

        return self._keyboard

    @property
    def typing(self) -> Typing:

        return self._typing

    @property
    def hotkeys(self) -> Hotkeys:

        return self._hotkeys

    @property
    def scrolling(self) -> Scrolling:

        return self._scrolling

    @property
    def clipboard(self) -> Clipboard:

        return self._clipboard

    @property
    def gestures(self) -> Gestures:

        return self._gestures

    @property
    def shortcuts(self) -> Shortcuts:

        return self._shortcuts

    # ---------------------------------------------------------
    # Convenience Methods
    # ---------------------------------------------------------

    def move_mouse(
        self,
        x: int,
        y: int,
        *,
        duration: float = 0.0,
    ) -> None:

        self._mouse.move_to(
            x,
            y,
            duration=duration,
        )

    def click(self) -> None:

        self._mouse.click()

    def type_text(
        self,
        text: str,
    ) -> None:

        self._typing.type_text(
            text,
        )

    def paste_text(
        self,
        text: str,
    ) -> None:

        self._typing.paste_text(
            text,
        )

    def copy(
        self,
    ) -> None:

        self._hotkeys.copy()

    def paste(
        self,
    ) -> None:

        self._hotkeys.paste()

    # ---------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------

    def move_and_click(
        self,
        x: int,
        y: int,
        *,
        duration: float = 0.0,
    ) -> None:

        self._mouse.move_to(
            x,
            y,
            duration=duration,
        )

        self._mouse.click()

    def drag_and_drop(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        *,
        duration: float = 0.2,
    ) -> None:

        self._gestures.drag_and_drop(
            start_x,
            start_y,
            end_x,
            end_y,
            duration=duration,
        )

    def scroll_up(
        self,
        clicks: int = 5,
    ) -> None:

        self._scrolling.up(
            clicks,
        )

    def scroll_down(
        self,
        clicks: int = 5,
    ) -> None:

        self._scrolling.down(
            clicks,
        )

    def get_clipboard(
        self,
    ) -> str:

        return self._clipboard.get_text()

    def set_clipboard(
        self,
        text: str,
    ) -> None:

        self._clipboard.set_text(
            text,
        )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "initialized": self._initialized,
            "mouse": repr(
                self._mouse,
            ),
            "keyboard": repr(
                self._keyboard,
            ),
            "typing": repr(
                self._typing,
            ),
            "hotkeys": repr(
                self._hotkeys,
            ),
            "scrolling": repr(
                self._scrolling,
            ),
            "clipboard": repr(
                self._clipboard,
            ),
            "gestures": repr(
                self._gestures,
            ),
            "shortcuts": repr(
                self._shortcuts,
            ),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "InputManager(" f"initialized={self._initialized})"
