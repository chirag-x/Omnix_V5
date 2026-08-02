"""
Omnix V5
Smart Click

Safe UI element interaction.
"""

from __future__ import annotations

import logging

from .ui_locator import (
    UILocator,
    UIElement,
)

from .ui_verifier import (
    UIVerifier,
)

from .ui_actions import (
    UIActions,
)

logger = logging.getLogger(__name__)


class SmartClick:
    """
    Intelligent UI clicking system.

    Combines:
    - Locator
    - Verifier
    - Actions
    """

    def __init__(
        self,
        locator: UILocator | None = None,
        verifier: UIVerifier | None = None,
        actions: UIActions | None = None,
    ) -> None:

        self._locator = locator or UILocator()

        self._verifier = verifier or UIVerifier()

        self._actions = actions or UIActions()

    # ---------------------------------------------------------
    # Click Element
    # ---------------------------------------------------------

    def click(
        self,
        element: UIElement,
    ) -> bool:
        """
        Verify and click element.
        """

        if not self._verifier.verify(
            element,
        ):

            logger.warning("Invalid UI element")

            return False

        return self._actions.click(
            element,
        )

    # ---------------------------------------------------------
    # Click By Name
    # ---------------------------------------------------------

    def click_text(
        self,
        text: str,
    ) -> bool:
        """
        Find element by text and click.
        """

        element = self._locator.find(
            text,
        )

        if element is None:

            logger.warning(
                "UI element not found: %s",
                text,
            )

            return False

        return self.click(
            element,
        )

    # ---------------------------------------------------------
    # Click Contains
    # ---------------------------------------------------------

    def click_contains(
        self,
        text: str,
    ) -> bool:
        """
        Click first matching element.
        """

        elements = self._locator.find_contains(
            text,
        )

        if not elements:

            return False

        return self.click(
            elements[0],
        )

    # ---------------------------------------------------------
    # Double Click
    # ---------------------------------------------------------

    def double_click_text(
        self,
        text: str,
    ) -> bool:

        element = self._locator.find(
            text,
        )

        if not self._verifier.verify(
            element,
        ):

            return False

        return self._actions.double_click(
            element,
        )

    # ---------------------------------------------------------
    # Move Cursor
    # ---------------------------------------------------------

    def move_to_text(
        self,
        text: str,
    ) -> bool:

        element = self._locator.find(
            text,
        )

        if not self._verifier.verify(
            element,
        ):

            return False

        return self._actions.move_to(
            element,
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "locator": repr(self._locator),
            "verifier": repr(self._verifier),
            "actions": repr(self._actions),
        }

    def __repr__(
        self,
    ) -> str:

        return "SmartClick()"
