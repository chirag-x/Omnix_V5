"""
Omnix V5
Gesture Controller
"""

from __future__ import annotations

import logging

from .mouse import Mouse

logger = logging.getLogger(__name__)


class Gestures:
    """
    High-level mouse gestures.

    Provides:

        • Drag & Drop
        • Box Selection
        • Swipe
        • Click & Drag
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
    # Drag & Drop
    # ---------------------------------------------------------

    def drag_and_drop(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        *,
        duration: float = 0.2,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.move_to(
            start_x,
            start_y,
        )

        self._mouse.mouse_down()

        self._mouse.drag_to(
            end_x,
            end_y,
            duration=duration,
        )

        self._mouse.mouse_up()

    # ---------------------------------------------------------
    # Selection
    # ---------------------------------------------------------

    def box_select(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        *,
        duration: float = 0.2,
    ) -> None:

        self.drag_and_drop(
            start_x,
            start_y,
            end_x,
            end_y,
            duration=duration,
        )

    # ---------------------------------------------------------
    # Swipe
    # ---------------------------------------------------------

    def swipe_left(
        self,
        distance: int = 200,
        *,
        duration: float = 0.2,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.mouse_down()

        self._mouse.drag_relative(
            -distance,
            0,
            duration=duration,
        )

        self._mouse.mouse_up()

    def swipe_right(
        self,
        distance: int = 200,
        *,
        duration: float = 0.2,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.mouse_down()

        self._mouse.drag_relative(
            distance,
            0,
            duration=duration,
        )

        self._mouse.mouse_up()

    def swipe_up(
        self,
        distance: int = 200,
        *,
        duration: float = 0.2,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.mouse_down()

        self._mouse.drag_relative(
            0,
            -distance,
            duration=duration,
        )

        self._mouse.mouse_up()

    def swipe_down(
        self,
        distance: int = 200,
        *,
        duration: float = 0.2,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.mouse_down()

        self._mouse.drag_relative(
            0,
            distance,
            duration=duration,
        )

        self._mouse.mouse_up()

    # ---------------------------------------------------------
    # Click & Drag
    # ---------------------------------------------------------

    def click_and_drag(
        self,
        dx: int,
        dy: int,
        *,
        duration: float = 0.2,
    ) -> None:

        if not self._enabled:
            return

        self._mouse.mouse_down()

        self._mouse.drag_relative(
            dx,
            dy,
            duration=duration,
        )

        self._mouse.mouse_up()

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

        return "Gestures(" f"enabled={self._enabled})"
