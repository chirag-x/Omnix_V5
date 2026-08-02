"""
Omnix V5
UI Navigation

Handles navigation between UI states.
"""

from __future__ import annotations

import logging
import time


from .ui_actions import (
    UIActions,
)

from .ui_waiter import (
    UIWaiter,
)

from .ui_verifier import (
    UIVerifier,
)


logger = logging.getLogger(__name__)


class UINavigation:
    """
    Controls navigation workflows.
    """


    def __init__(
        self,
        actions: UIActions | None = None,
        waiter: UIWaiter | None = None,
        verifier: UIVerifier | None = None,
    ) -> None:


        self._actions = (
            actions
            or UIActions()
        )


        self._waiter = (
            waiter
            or UIWaiter()
        )


        self._verifier = (
            verifier
            or UIVerifier()
        )


        self._history: list[str] = []


    # ---------------------------------------------------------
    # Navigate
    # ---------------------------------------------------------

    def navigate(
        self,
        steps: list[dict],
    ) -> bool:
        """
        Execute navigation steps.

        Example:

        [
            {
                "action":"click",
                "target":"Settings"
            }
        ]
        """


        for step in steps:

            action = step.get(
                "action",
            )


            target = step.get(
                "target",
            )


            if action == "click":

                if not self.click_target(
                    target,
                ):

                    return False


            elif action == "wait":

                if not self.wait_target(
                    target,
                ):

                    return False


            else:

                logger.warning(
                    "Unknown navigation action: %s",
                    action,
                )

                return False


            self._history.append(
                str(target),
            )


        return True


    # ---------------------------------------------------------
    # Click Target
    # ---------------------------------------------------------

    def click_target(
        self,
        target: str,
    ) -> bool:


        from .ui_locator import UILocator


        locator = UILocator()


        element = locator.find(
            target,
        )


        if not self._verifier.verify(
            element,
        ):

            logger.warning(
                "Navigation target unavailable: %s",
                target,
            )

            return False


        return self._actions.click(
            element,
        )


    # ---------------------------------------------------------
    # Wait Target
    # ---------------------------------------------------------

    def wait_target(
        self,
        target: str,
        timeout: float = 5.0,
    ) -> bool:


        element = self._waiter.wait_for(
            target,
            timeout,
        )


        return (
            element is not None
        )


    # ---------------------------------------------------------
    # History
    # ---------------------------------------------------------

    def history(
        self,
    ) -> list[str]:

        return self._history.copy()


    def clear_history(
        self,
    ) -> None:

        self._history.clear()


    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {

            "navigation_steps":
                len(self._history),

        }


    def __repr__(
        self,
    ) -> str:

        return (
            "UINavigation("
            f"steps={len(self._history)})"
        )