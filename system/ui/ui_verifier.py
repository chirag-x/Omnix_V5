"""
Omnix V5
UI Verifier

Validates UI elements before interaction.
"""

from __future__ import annotations

import logging

from .ui_locator import UIElement

logger = logging.getLogger(__name__)


class UIVerifier:
    """
    Verifies detected UI elements.
    """

    def __init__(
        self,
        minimum_confidence: float = 0.5,
    ) -> None:

        self._minimum_confidence = minimum_confidence

    # ---------------------------------------------------------
    # Element Verification
    # ---------------------------------------------------------

    def verify(
        self,
        element: UIElement | None,
    ) -> bool:
        """
        Verify if element is usable.
        """

        if element is None:

            return False

        if not element.name:

            return False

        if element.width <= 0:

            return False

        if element.height <= 0:

            return False

        if element.confidence < self._minimum_confidence:

            return False

        return True

    # ---------------------------------------------------------
    # Position Verification
    # ---------------------------------------------------------

    def valid_position(
        self,
        element: UIElement,
        screen_width: int,
        screen_height: int,
    ) -> bool:
        """
        Check if element exists on screen.
        """

        if element.x < 0:

            return False

        if element.y < 0:

            return False

        if element.x + element.width > screen_width:

            return False

        if element.y + element.height > screen_height:

            return False

        return True

    # ---------------------------------------------------------
    # Confidence
    # ---------------------------------------------------------

    def confidence(
        self,
        element: UIElement,
    ) -> float:

        return element.confidence

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "minimum_confidence": self._minimum_confidence,
        }

    def __repr__(
        self,
    ) -> str:

        return "UIVerifier(" f"confidence={self._minimum_confidence})"
