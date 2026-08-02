"""
Omnix V5
UI Waiter

Waits for UI elements and conditions.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from .ui_locator import (
    UILocator,
    UIElement,
)

logger = logging.getLogger(__name__)


class UIWaiter:
    """
    Handles waiting for UI states.
    """

    def __init__(
        self,
        locator: UILocator | None = None,
    ) -> None:

        self._locator = locator or UILocator()

    # ---------------------------------------------------------
    # Wait For Element
    # ---------------------------------------------------------

    def wait_for(
        self,
        name: str,
        timeout: float = 5.0,
        interval: float = 0.2,
    ) -> UIElement | None:
        """
        Wait until an element appears.
        """

        start = time.time()

        while time.time() - start < timeout:

            element = self._locator.find(
                name,
            )

            if element:

                return element

            time.sleep(
                interval,
            )

        return None

    # ---------------------------------------------------------
    # Wait Contains
    # ---------------------------------------------------------

    def wait_contains(
        self,
        text: str,
        timeout: float = 5.0,
        interval: float = 0.2,
    ) -> list[UIElement]:
        """
        Wait for matching elements.
        """

        start = time.time()

        while time.time() - start < timeout:

            elements = self._locator.find_contains(
                text,
            )

            if elements:

                return elements

            time.sleep(
                interval,
            )

        return []

    # ---------------------------------------------------------
    # Generic Condition
    # ---------------------------------------------------------

    def wait_until(
        self,
        condition: Callable,
        timeout: float = 5.0,
        interval: float = 0.2,
    ) -> bool:
        """
        Wait for any condition.
        """

        start = time.time()

        while time.time() - start < timeout:

            try:

                if condition():

                    return True

            except Exception as exc:

                logger.debug(
                    "Wait condition failed: %s",
                    exc,
                )

            time.sleep(
                interval,
            )

        return False

    # ---------------------------------------------------------
    # Delay
    # ---------------------------------------------------------

    def sleep(
        self,
        seconds: float,
    ) -> None:

        time.sleep(
            seconds,
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "locator": repr(self._locator),
        }

    def __repr__(
        self,
    ) -> str:

        return "UIWaiter()"
