"""
Omnix V5
UI Actions

Performs UI interactions.
"""

from __future__ import annotations

import logging

from .ui_locator import UIElement

from system.services.ui_controller import (
    UIController,
)

logger = logging.getLogger(__name__)


class UIActions:
    """
    Executes actions on UI elements.
    """

    def __init__(
        self,
        controller: UIController | None = None,
    ) -> None:

        self._controller = controller or UIController()

    # ---------------------------------------------------------
    # Click
    # ---------------------------------------------------------

    def click(
        self,
        element: UIElement,
    ) -> bool:
        """
        Click center of element.
        """

        if element is None:

            return False

        x, y = element.center

        return self._controller.click(
            x,
            y,
        )

    def double_click(
        self,
        element: UIElement,
    ) -> bool:

        if element is None:

            return False

        x, y = element.center

        return self._controller.double_click(
            x,
            y,
        )

    # ---------------------------------------------------------
    # Typing
    # ---------------------------------------------------------

    def type_text(
        self,
        text: str,
    ) -> bool:

        return self._controller.type_text(
            text,
        )

    def press_key(
        self,
        key: str,
    ) -> bool:

        return self._controller.press_key(
            key,
        )

    def hotkey(
        self,
        *keys: str,
    ) -> bool:

        return self._controller.hotkey(
            *keys,
        )

    # ---------------------------------------------------------
    # Move
    # ---------------------------------------------------------

    def move_to(
        self,
        element: UIElement,
    ) -> bool:

        if element is None:

            return False

        x, y = element.center

        return self._controller.move_cursor(
            x,
            y,
        )

    # ---------------------------------------------------------
    # Screenshot
    # ---------------------------------------------------------

    def screenshot(
        self,
        path: str | None = None,
    ):

        return self._controller.screenshot(
            path,
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "controller": repr(self._controller),
        }

    def __repr__(
        self,
    ) -> str:

        return "UIActions()"
