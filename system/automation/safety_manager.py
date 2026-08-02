"""
Omnix V5
Safety Manager

Performs safety validation before automation actions are executed.
"""

from __future__ import annotations

import logging

from system.models.action import Action

logger = logging.getLogger(__name__)


class SafetyManager:
    """
    Validates whether automation actions are safe to execute.

    This class provides centralized safety checks before
    actions reach the ActionExecutor.
    """

    def __init__(self) -> None:

        self._enabled = True

        self._blocked_actions: set[str] = set()

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
    # Validation
    # ---------------------------------------------------------

    def validate(
        self,
        action: Action,
    ) -> bool:

        if not self._enabled:

            return True

        action_type = getattr(
            action,
            "action_type",
            None,
        )

        if action_type in self._blocked_actions:

            logger.warning(
                "Blocked action: %s",
                action_type,
            )

            return False

        return True

    # ---------------------------------------------------------
    # Rules
    # ---------------------------------------------------------

    def block_action(
        self,
        action_type: str,
    ) -> None:

        self._blocked_actions.add(
            action_type,
        )

    def allow_action(
        self,
        action_type: str,
    ) -> None:

        self._blocked_actions.discard(
            action_type,
        )

    def clear_rules(
        self,
    ) -> None:

        self._blocked_actions.clear()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def blocked_actions(
        self,
    ) -> set[str]:

        return set(
            self._blocked_actions,
        )

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
            "blocked_actions": len(
                self._blocked_actions,
            ),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return (
            "SafetyManager("
            f"enabled={self._enabled}, "
            f"blocked_actions={len(self._blocked_actions)})"
        )
