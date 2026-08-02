"""
Omnix V5
Scrolling Controller
"""

from __future__ import annotations

import logging

from .mouse import Mouse

logger = logging.getLogger(__name__)


class Scrolling:
    """
    High-level scrolling controller.

    Provides:

        • Scroll up
        • Scroll down
        • Page up
        • Page down
        • Scroll to top
        • Scroll to bottom
    """

    def __init__(
        self,
    ) -> None:

        self._mouse = Mouse()

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

        self._mouse.enable()

    def disable(
        self,
    ) -> None:

        self._enabled = False

        self._mouse.disable()

    # ---------------------------------------------------------
    # Basic Scrolling
    # ---------------------------------------------------------

    def up(
        self,
        clicks: int = 5,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.scroll(clicks)

    def down(
        self,
        clicks: int = 5,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.scroll(-clicks)

    # ---------------------------------------------------------
    # Page Scrolling
    # ---------------------------------------------------------

    def page_up(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.scroll(20)

    def page_down(
        self,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.scroll(-20)

    # ---------------------------------------------------------
    # Horizontal
    # ---------------------------------------------------------

    def left(
        self,
        clicks: int = 5,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.horizontal_scroll(
            -clicks,
        )

    def right(
        self,
        clicks: int = 5,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.horizontal_scroll(
            clicks,
        )
    # ---------------------------------------------------------
    # Custom Scrolling
    # ---------------------------------------------------------

    def scroll(
        self,
        clicks: int,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.scroll(clicks)

    def horizontal(
        self,
        clicks: int,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.horizontal_scroll(
            clicks,
        )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def mouse(
        self,
    ) -> Mouse:

        return self._mouse

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

        return (
            "Scrolling("
            f"enabled={self._enabled})"
        )