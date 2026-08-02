"""
Omnix V5
Accessibility

Accessibility based UI discovery.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AccessibleElement:
    """
    Represents an accessibility UI element.
    """

    name: str

    role: str

    enabled: bool = True

    visible: bool = True

    value: str | None = None


class AccessibilityManager:
    """
    Handles accessibility based UI information.
    """

    def __init__(
        self,
    ) -> None:

        self._elements: list[AccessibleElement] = []

    # ---------------------------------------------------------
    # Register
    # ---------------------------------------------------------

    def add(
        self,
        element: AccessibleElement,
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
    ) -> AccessibleElement | None:

        name = name.lower()

        for element in self._elements:

            if element.name.lower() == name:

                return element

        return None

    def find_role(
        self,
        role: str,
    ) -> list[AccessibleElement]:

        role = role.lower()

        return [element for element in self._elements if element.role.lower() == role]

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def is_available(
        self,
        element: AccessibleElement | None,
    ) -> bool:

        if element is None:

            return False

        return element.enabled and element.visible

    # ---------------------------------------------------------
    # Backend Update
    # ---------------------------------------------------------

    def update_from_tree(
        self,
        tree: list[dict],
    ) -> None:
        """
        Convert accessibility tree data.
        """

        self.clear()

        for item in tree:

            try:

                self.add(
                    AccessibleElement(
                        name=item.get(
                            "name",
                            "",
                        ),
                        role=item.get(
                            "role",
                            "",
                        ),
                        enabled=item.get(
                            "enabled",
                            True,
                        ),
                        visible=item.get(
                            "visible",
                            True,
                        ),
                        value=item.get(
                            "value",
                        ),
                    )
                )

            except Exception as exc:

                logger.error(
                    "Accessibility update failed: %s",
                    exc,
                )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def elements(
        self,
    ) -> list[AccessibleElement]:

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

        return "AccessibilityManager(" f"elements={len(self._elements)})"
