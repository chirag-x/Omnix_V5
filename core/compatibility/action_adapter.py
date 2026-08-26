"""
Omnix V5 - Action Compatibility Adapter

Centralized compatibility layer for converting legacy,
alternate, and V5 action formats into a single normalized
action representation.

Normalized format:

{
    "action": "open_application",
    "parameters": {
        "app": "chrome"
    }
}

This module does NOT execute actions.
It only normalizes action names and parameters.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

# ============================================================================
# ACTION ALIASES
# ============================================================================
#
# Maps legacy / alternate action names to the canonical V5 action names.
#

ACTION_ALIASES: Dict[str, str] = {
    # ------------------------------------------------------------------------
    # APPLICATIONS
    # ------------------------------------------------------------------------
    "open_app": "open_application",
    "launch_app": "open_application",
    "start_app": "open_application",
    "run_app": "open_application",
    "close_app": "close_application",
    "quit_app": "close_application",
    "exit_app": "close_application",
    "kill_app": "close_application",
    "focus_app": "focus_application",
    "activate_app": "focus_application",
    # ------------------------------------------------------------------------
    # BROWSER
    # ------------------------------------------------------------------------
    "open_url": "navigate",
    "go_to": "navigate",
    "goto": "navigate",
    "visit": "navigate",
    "search": "search_web",
    "web_search": "search_web",
    "search_google": "search_web",
    "google_search": "search_web",
    "open_web_browser": "open_browser",
    "launch_browser": "open_browser",
    "reload": "refresh_browser",
    "refresh": "refresh_browser",
    "back": "browser_back",
    "go_back": "browser_back",
    "forward": "browser_forward",
    "go_forward": "browser_forward",
    "scroll_page": "scroll",
    "scroll_browser_page": "scroll_browser",
    # ------------------------------------------------------------------------
    # MOUSE
    # ------------------------------------------------------------------------
    "click_mouse": "click",
    "mouse_click": "click",
    "doubleclick": "double_click",
    "double_click_mouse": "double_click",
    "rightclick": "right_click",
    "right_click_mouse": "right_click",
    "middleclick": "middle_click",
    "middle_click_mouse": "middle_click",
    "move": "move_mouse",
    "mouse_move": "move_mouse",
    "drag_mouse": "drag",
    "mouse_drag": "drag",
    "click_ui": "click",
    # ------------------------------------------------------------------------
    # KEYBOARD / TEXT
    # ------------------------------------------------------------------------
    "type": "type_text",
    "write": "type_text",
    "input_text": "type_text",
    "enter_text": "type_text",
    "press": "press_key",
    "key_press": "press_key",
    "shortcut": "hotkey",
    "keyboard_shortcut": "hotkey",
    # ------------------------------------------------------------------------
    # SYSTEM
    # ------------------------------------------------------------------------
    "wait": "sleep",
    "delay": "sleep",
}


# ============================================================================
# CANONICAL ACTIONS
# ============================================================================

CANONICAL_ACTIONS = frozenset(
    {
        # Applications
        "open_application",
        "close_application",
        "focus_application",
        # Browser
        "open_browser",
        "search_web",
        "navigate",
        "new_tab",
        "close_tab",
        "refresh_browser",
        "browser_back",
        "browser_forward",
        "scroll_browser",
        "focus_browser",
        # Mouse
        "move_mouse",
        "click",
        "double_click",
        "right_click",
        "middle_click",
        "drag",
        # Keyboard
        "type_text",
        "press_key",
        "hotkey",
        # Screen / scrolling
        "scroll",
        # Utility
        "sleep",
    }
)


# ============================================================================
# ACTION ADAPTER
# ============================================================================


class ActionAdapter:
    """
    Converts actions from different Omnix versions and
    formats into the canonical V5 action format.

    Supported input examples:

        {"skill": "open_app", "parameters": {"app": "chrome"}}

        {"action": "open_application", "parameters": {"app": "chrome"}}

        {
            "tool": "type",
            "params": {"value": "Hello"}
        }

    All valid inputs are normalized to:

        {
            "action": "...",
            "parameters": {...}
        }
    """

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    @classmethod
    def adapt(
        cls,
        action: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize an action into the V5 format.

        Returns None if the action cannot be normalized.
        """

        if action is None:
            return None

        if isinstance(action, str):

            return cls._build_normalized(
                action_name=action,
                parameters={},
            )

        if not isinstance(action, dict):
            return None

        action_name = cls._extract_action_name(action)

        if not action_name:
            return None

        parameters = cls._extract_parameters(action)

        return cls._build_normalized(
            action_name=action_name,
            parameters=parameters,
        )

    @classmethod
    def adapt_many(
        cls,
        actions: Any,
    ) -> list[Dict[str, Any]]:
        """
        Normalize multiple actions.

        Invalid actions are ignored.
        """

        if actions is None:
            return []

        if isinstance(actions, dict):
            actions = [actions]

        if isinstance(actions, str):
            actions = [actions]

        try:
            iterator = iter(actions)
        except TypeError:
            return []

        normalized_actions = []

        for action in iterator:

            normalized = cls.adapt(action)

            if normalized is not None:
                normalized_actions.append(normalized)

        return normalized_actions

    @classmethod
    def normalize_action_name(
        cls,
        action_name: Any,
    ) -> Optional[str]:
        """
        Convert an action name to its canonical V5 name.
        """

        if action_name is None:
            return None

        normalized = str(action_name).strip().lower()

        if not normalized:
            return None

        normalized = normalized.replace("-", "_").replace(" ", "_")

        return ACTION_ALIASES.get(
            normalized,
            normalized,
        )

    @classmethod
    def is_canonical(
        cls,
        action_name: Any,
    ) -> bool:
        """
        Return True if the action is already a canonical V5 action.
        """

        normalized = cls.normalize_action_name(action_name)

        return normalized in CANONICAL_ACTIONS

    # ========================================================================
    # EXTRACTION
    # ========================================================================

    @staticmethod
    def _extract_action_name(
        action: Dict[str, Any],
    ) -> Optional[str]:

        for key in (
            "action",
            "skill",
            "tool",
            "name",
            "command",
        ):

            value = action.get(key)

            if value is None:
                continue

            value = str(value).strip()

            if value:
                return value

        return None

    @classmethod
    def _extract_parameters(
        cls,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:

        parameters: Dict[str, Any] = {}

        for key in (
            "parameters",
            "params",
            "kwargs",
            "arguments",
        ):

            value = action.get(key)

            if isinstance(value, dict):
                parameters.update(deepcopy(value))

                reserved_keys = {
                    # Action identity
                    "action",
                    "skill",
                    "tool",
                    "name",
                    "command",
                    # Parameter containers
                    "parameters",
                    "params",
                    "kwargs",
                    "arguments",
                    "args",
                    # General metadata
                    "metadata",
                    # Workflow / step identity
                    "id",
                    "step_id",
                    "task_id",
                    "plan_id",
                    "workflow_id",
                    # Workflow structure
                    "description",
                    "dependencies",
                    "depends_on",
                    "requires",
                    # Workflow execution state
                    "status",
                    "result",
                    "error",
                    # Internal compatibility / execution data
                    "payload",
                    "source_plan",
                    "original_action",
                }

        for key, value in action.items():

            if key in reserved_keys:
                continue

            parameters.setdefault(
                key,
                deepcopy(value),
            )

        return parameters

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    @classmethod
    def _build_normalized(
        cls,
        *,
        action_name: Any,
        parameters: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        original_action = str(action_name).strip()

        if not original_action:
            return None

        normalized_action = cls.normalize_action_name(original_action)

        if not normalized_action:
            return None

        normalized_parameters = deepcopy(parameters)

        cls._normalize_parameters(
            normalized_action,
            normalized_parameters,
        )

        return {
            "action": normalized_action,
            "parameters": normalized_parameters,
            "original_action": (
                original_action.lower().replace("-", "_").replace(" ", "_")
            ),
        }

    # ========================================================================
    # PARAMETER NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_parameters(
        action: str,
        parameters: Dict[str, Any],
    ) -> None:

        # --------------------------------------------------------------------
        # APPLICATION PARAMETERS
        # --------------------------------------------------------------------

        if action in {
            "open_application",
            "close_application",
            "focus_application",
        }:

            ActionAdapter._rename_parameter(
                parameters,
                "application",
                "app",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "program",
                "app",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "name",
                "app",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "target",
                "app",
            )

        # --------------------------------------------------------------------
        # TEXT PARAMETERS
        # --------------------------------------------------------------------

        if action == "type_text":

            ActionAdapter._rename_parameter(
                parameters,
                "value",
                "text",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "message",
                "text",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "content",
                "text",
            )

        # --------------------------------------------------------------------
        # KEY PARAMETERS
        # --------------------------------------------------------------------

        if action == "press_key":

            ActionAdapter._rename_parameter(
                parameters,
                "keys",
                "key",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "button",
                "key",
            )

        # --------------------------------------------------------------------
        # URL PARAMETERS
        # --------------------------------------------------------------------

        if action == "navigate":

            ActionAdapter._rename_parameter(
                parameters,
                "link",
                "url",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "website",
                "url",
            )

        # --------------------------------------------------------------------
        # SEARCH PARAMETERS
        # --------------------------------------------------------------------

        if action == "search_web":

            ActionAdapter._rename_parameter(
                parameters,
                "query",
                "query",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "search",
                "query",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "text",
                "query",
            )

        # --------------------------------------------------------------------
        # MOUSE POSITION PARAMETERS
        # --------------------------------------------------------------------

        for old_name, new_name in {
            "pos_x": "x",
            "pos_y": "y",
        }.items():

            ActionAdapter._rename_parameter(
                parameters,
                old_name,
                new_name,
            )

        # --------------------------------------------------------------------
        # DRAG PARAMETERS
        # --------------------------------------------------------------------

        if action == "drag":

            aliases = {
                "x1": "start_x",
                "y1": "start_y",
                "x2": "end_x",
                "y2": "end_y",
                "from_x": "start_x",
                "from_y": "start_y",
                "to_x": "end_x",
                "to_y": "end_y",
            }

            for old_name, new_name in aliases.items():

                ActionAdapter._rename_parameter(
                    parameters,
                    old_name,
                    new_name,
                )

        # --------------------------------------------------------------------
        # SCROLL PARAMETERS
        # --------------------------------------------------------------------

        if action in {
            "scroll",
            "scroll_browser",
        }:

            if "amount" not in parameters:

                direction = (
                    str(
                        parameters.get(
                            "direction",
                            "",
                        )
                    )
                    .strip()
                    .lower()
                )

                if direction == "up":
                    parameters["amount"] = 3

                elif direction == "down":
                    parameters["amount"] = -3

            ActionAdapter._rename_parameter(
                parameters,
                "scroll_amount",
                "amount",
            )

        # --------------------------------------------------------------------
        # SLEEP PARAMETERS
        # --------------------------------------------------------------------

        if action == "sleep":

            ActionAdapter._rename_parameter(
                parameters,
                "seconds",
                "duration",
            )

            ActionAdapter._rename_parameter(
                parameters,
                "time",
                "duration",
            )

    # ========================================================================
    # UTILITY
    # ========================================================================

    @staticmethod
    def _rename_parameter(
        parameters: Dict[str, Any],
        old_name: str,
        new_name: str,
    ) -> None:

        if new_name not in parameters and old_name in parameters:

            parameters[new_name] = parameters.pop(old_name)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def adapt_action(
    action: Any,
) -> Optional[Dict[str, Any]]:

    return ActionAdapter.adapt(action)


def adapt_actions(
    actions: Any,
) -> list[Dict[str, Any]]:

    return ActionAdapter.adapt_many(actions)


def normalize_action_name(
    action_name: Any,
) -> Optional[str]:

    return ActionAdapter.normalize_action_name(action_name)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ACTION_ALIASES",
    "CANONICAL_ACTIONS",
    "ActionAdapter",
    "adapt_action",
    "adapt_actions",
    "normalize_action_name",
]
