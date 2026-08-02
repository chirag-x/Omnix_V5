"""
Omnix V5
OCR Locator

Converts OCR results into UI elements.
"""

from __future__ import annotations

import logging

from .ui_locator import (
    UILocator,
    UIElement,
)

logger = logging.getLogger(__name__)


class OCRLocator:
    """
    Handles OCR based UI element detection.
    """

    def __init__(
        self,
        locator: UILocator | None = None,
    ) -> None:

        self._locator = locator or UILocator()

    # ---------------------------------------------------------
    # Process OCR Results
    # ---------------------------------------------------------

    def process(
        self,
        results: list[dict],
    ) -> list[UIElement]:
        """
        Convert OCR results into UI elements.
        """

        elements = []

        for item in results:

            try:

                element = UIElement(
                    name=item.get(
                        "text",
                        "",
                    ),
                    x=item.get(
                        "x",
                        0,
                    ),
                    y=item.get(
                        "y",
                        0,
                    ),
                    width=item.get(
                        "width",
                        0,
                    ),
                    height=item.get(
                        "height",
                        0,
                    ),
                    confidence=item.get(
                        "confidence",
                        1.0,
                    ),
                )

                elements.append(
                    element,
                )

            except Exception as exc:

                logger.error(
                    "OCR conversion failed: %s",
                    exc,
                )

        self._locator.clear()

        for element in elements:

            self._locator.add(
                element,
            )

        return elements

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def find_text(
        self,
        text: str,
    ) -> UIElement | None:

        return self._locator.find(
            text,
        )

    def find_contains(
        self,
        text: str,
    ) -> list[UIElement]:

        return self._locator.find_contains(
            text,
        )

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    def elements(
        self,
    ) -> list[UIElement]:

        return self._locator.all()

    def statistics(
        self,
    ) -> dict:

        return {
            "elements": len(self._locator.all()),
        }

    def __repr__(
        self,
    ) -> str:

        return "OCRLocator(" f"elements={len(self._locator.all())})"
