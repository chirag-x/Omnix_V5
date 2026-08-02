"""
Omnix V5
Verification

Verifies automation execution results.
"""

from __future__ import annotations

import logging

from system.models.action import Action
from system.models.action_result import ActionResult

logger = logging.getLogger(__name__)


class Verification:
    """
    Verifies whether an action completed successfully.

    This class performs lightweight validation of
    ActionResult objects. More advanced verification
    (vision, OCR, UI inspection) can be added later.
    """

    def __init__(self) -> None:

        self._enabled = True

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def enabled(self) -> bool:

        return self._enabled

    def enable(self) -> None:

        self._enabled = True

    def disable(self) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Verification
    # ---------------------------------------------------------

    def verify(
        self,
        action: Action,
        result: ActionResult,
    ) -> bool:

        if not self._enabled:
            return True

        logger.debug(
            "Verifying action: %s",
            action,
        )

        return result.success

    def verify_batch(
        self,
        actions: list[Action],
        results: list[ActionResult],
    ) -> bool:

        if len(actions) != len(results):

            return False

        return all(

            self.verify(
                action,
                result,
            )

            for action, result

            in zip(
                actions,
                results,
            )

        )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

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

        return (

            "Verification("

            f"enabled={self._enabled})"

        )