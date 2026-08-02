"""
Omnix V5
UI Locator

Finds UI elements.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UIElement:
    """
    Represents a detected UI element.
    """

    name: str

    x: int

    y: int

    width: int

    height: int

    confidence: float = 1.0

    @property
    def center(
        self,
    ) -> tuple[int, int]:

        return (
            self.x + self.width // 2,
            self.y + self.height // 2,
        )


class UILocator:
    """
    Locates UI elements.
    """

    def __init__(
        self,
    ) -> None:

        self._elements: list[UIElement] = []

    # ---------------------------------------------------------
    # Register Elements
    # ---------------------------------------------------------

    def add(
        self,
        element: UIElement,
    ) -> None:

        self._elements.append(
            element,
        )

    def clear(
        self,
    ) -> None:

        self._elements.clear()

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def find(
        self,
        name: str,
    ) -> UIElement | None:

        name = name.lower()

        for element in self._elements:

            if element.name.lower() == name:

                return element

        return None

    def find_contains(
        self,
        text: str,
    ) -> list[UIElement]:

        text = text.lower()

        return [element for element in self._elements if text in element.name.lower()]

    # ---------------------------------------------------------
    # Vision Update
    # ---------------------------------------------------------

    def update_from_detection(
        self,
        detections: list[dict],
    ) -> None:
        """
        Add elements from vision/OCR output.
        """

        self.clear()

        for item in detections:

            try:

                self.add(
                    UIElement(
                        name=item["name"],
                        x=item["x"],
                        y=item["y"],
                        width=item["width"],
                        height=item["height"],
                        confidence=item.get(
                            "confidence",
                            1.0,
                        ),
                    )
                )

            except Exception as exc:

                logger.error(
                    "UI element update failed: %s",
                    exc,
                )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def all(
        self,
    ) -> list[UIElement]:

        return self._elements.copy()

    def statistics(
        self,
    ) -> dict:

        return {
            "elements": len(self._elements),
        }

    def __repr__(
        self,
    ) -> str:

        return "UILocator(" f"elements={len(self._elements)})"
