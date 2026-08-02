"""
Omnix V5
Action Executor

Executes a single automation action.
"""

from __future__ import annotations

import logging
from typing import Any

from system.applications.application_manager import ApplicationManager
from system.input.input_manager import InputManager

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes individual automation actions.

    Each call executes exactly one action.
    """

    def __init__(
        self,
        applications: ApplicationManager,
        input_manager: InputManager,
    ) -> None:

        self._applications = applications

        self._input = input_manager

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
    # Execution
    # ---------------------------------------------------------

    def execute(
        self,
        action: dict[str, Any],
    ) -> Any:

        if not self._enabled:
            return None

        action_type = action.get(
            "type",
        )

        logger.debug(
            "Executing action: %s",
            action_type,
        )

        handlers = {
            "open_application": self._open_application,
            "close_application": self._close_application,
            "move_mouse": self._move_mouse,
            "click": self._click,
            "type_text": self._type_text,
            "press_key": self._press_key,
            "copy": self._copy,
            "paste": self._paste,
        }

        handler = handlers.get(
            action_type,
        )

        if handler is None:

            raise ValueError(f"Unknown action: {action_type}")

        return handler(
            action,
        )

    # ---------------------------------------------------------
    # Handlers
    # ---------------------------------------------------------

    def _open_application(
        self,
        action: dict[str, Any],
    ) -> Any:

        return self._applications.open(
            action["application"],
        )

    def _close_application(
        self,
        action: dict[str, Any],
    ) -> Any:

        return self._applications.close(
            action["application"],
        )

    def _move_mouse(
        self,
        action: dict[str, Any],
    ) -> None:

        self._input.mouse.move_to(
            action["x"],
            action["y"],
            duration=action.get(
                "duration",
                0,
            ),
        )

    def _click(
        self,
        action: dict[str, Any],
    ) -> None:

        self._input.mouse.click()

    def _type_text(
        self,
        action: dict[str, Any],
    ) -> None:

        self._input.typing.type_text(
            action["text"],
        )

    def _press_key(
        self,
        action: dict[str, Any],
    ) -> None:

        self._input.keyboard.press(
            action["key"],
        )

    def _copy(
        self,
        action: dict[str, Any],
    ) -> None:

        self._input.hotkeys.copy()

    def _paste(
        self,
        action: dict[str, Any],
    ) -> None:

        self._input.hotkeys.paste()

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "ActionExecutor(" f"enabled={self._enabled})"
