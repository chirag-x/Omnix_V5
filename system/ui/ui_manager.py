"""
Omnix V5
UI Manager

Central UI interaction manager.
"""

from __future__ import annotations

import logging


from .ui_locator import (
    UILocator,
)

from .ocr_locator import (
    OCRLocator,
)

from .ui_verifier import (
    UIVerifier,
)

from .ui_waiter import (
    UIWaiter,
)

from .ui_actions import (
    UIActions,
)

from .smart_click import (
    SmartClick,
)

from .ui_navigation import (
    UINavigation,
)

from .accessibility import (
    AccessibilityManager,
)

logger = logging.getLogger(__name__)


class UIManager:
    """
    Main controller for UI subsystem.
    """

    def __init__(
        self,
        locator=None,
        ocr=None,
        accessibility=None,
        verifier=None,
        waiter=None,
        actions=None,
    ):

        self.locator = locator or UILocator()

        self.ocr = ocr or OCRLocator(self.locator)

        self.accessibility = accessibility or AccessibilityManager()

        self.verifier = verifier or UIVerifier()

        self.waiter = waiter or UIWaiter(self.locator)

        self.actions = actions or UIActions()
        # Smart interaction

        self.smart_click = SmartClick(
            locator=self.locator,
            verifier=self.verifier,
            actions=self.actions,
        )

        # Navigation

        self.navigation = UINavigation(
            actions=self.actions,
            waiter=self.waiter,
            verifier=self.verifier,
        )

        self._enabled = True

    # ---------------------------------------------------------
    # State
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

    def disable(
        self,
    ) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Detection Updates
    # ---------------------------------------------------------

    def update_ocr(
        self,
        results: list[dict],
    ) -> None:
        """
        Update UI from OCR.
        """

        if not self._enabled:

            return

        self.ocr.process(
            results,
        )

    def update_accessibility(
        self,
        tree: list[dict],
    ) -> None:

        self.accessibility.update_from_tree(
            tree,
        )

    # ---------------------------------------------------------
    # Interaction
    # ---------------------------------------------------------

    def click(
        self,
        name: str,
    ) -> bool:

        if not self._enabled:

            return False

        return self.smart_click.click_text(
            name,
        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return (
            self.locator.find(
                name,
            )
            is not None
        )

    # ---------------------------------------------------------
    # Snapshot
    # ---------------------------------------------------------

    def elements(
        self,
    ) -> list:

        return self.locator.all()

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
            "elements": len(self.locator.all()),
            "locator": self.locator.statistics(),
            "ocr": self.ocr.statistics(),
            "accessibility": self.accessibility.statistics(),
        }

    def __repr__(
        self,
    ) -> str:

        return "UIManager(" f"enabled={self._enabled})"
