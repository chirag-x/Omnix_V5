"""
Omnix V5 - Plan Compatibility Adapter

Normalizes different planning formats used across Omnix into
a consistent list of V5-compatible action dictionaries.

Supported inputs include:

- list of action dictionaries
- legacy plans using "skill"
- dictionaries containing "steps"
- dictionaries containing "actions"
- TaskPlan-like objects
- Workflow-like objects
- TaskStep-like objects

Output format:

[
    {
        "action": "open_application",
        "parameters": {"app": "chrome"},
        "original_action": "open_app"
    }
]

This module does NOT execute plans.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.compatibility.action_adapter import adapt_action


class PlanAdapter:
    """
    Converts multiple Omnix plan representations into a
    normalized V5 action list.
    """

    @classmethod
    def adapt(
        cls,
        plan: Any,
    ) -> List[Dict[str, Any]]:
        """
        Normalize a plan into a list of V5 actions.
        """

        if plan is None:
            return []

        # ---------------------------------------------------------
        # Single action dictionary
        # ---------------------------------------------------------

        if isinstance(plan, dict):

            return cls._adapt_dict(plan)

        # ---------------------------------------------------------
        # Single action string
        # ---------------------------------------------------------

        if isinstance(plan, str):

            action = adapt_action(plan)

            return [action] if action else []

        # ---------------------------------------------------------
        # List / tuple / iterable
        # ---------------------------------------------------------

        if isinstance(plan, (list, tuple)):

            return cls._adapt_sequence(plan)

        # ---------------------------------------------------------
        # Object-based plans
        # ---------------------------------------------------------

        return cls._adapt_object(plan)

    @classmethod
    def adapt_step(
        cls,
        step: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize a single step into a V5 action.
        """

        if step is None:
            return None

        # Already dictionary-like.
        if isinstance(step, dict):

            return adapt_action(step)

        # Direct string action.
        if isinstance(step, str):

            return adapt_action(step)

        # Object-based step.
        step_dict = cls._object_to_dict(step)

        if not step_dict:
            return None

        return adapt_action(step_dict)

    @classmethod
    def is_plan(
        cls,
        value: Any,
    ) -> bool:
        """
        Return True if the value appears to represent a plan.
        """

        if value is None:
            return False

        if isinstance(value, (list, tuple)):
            return True

        if isinstance(value, dict):

            return any(
                key in value
                for key in (
                    "steps",
                    "actions",
                    "plan",
                    "workflow",
                    "tasks",
                )
            )

        return any(
            hasattr(value, attribute)
            for attribute in (
                "steps",
                "actions",
                "plan",
                "workflow",
                "tasks",
            )
        )

    # =============================================================
    # DICTIONARY ADAPTATION
    # =============================================================

    @classmethod
    def _adapt_dict(
        cls,
        plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        # If this dictionary itself is an action.
        if cls._looks_like_action(plan):

            action = adapt_action(plan)

            return [action] if action else []

        # Check common plan containers.
        for key in (
            "steps",
            "actions",
            "plan",
            "workflow",
            "tasks",
        ):

            if key not in plan:
                continue

            value = plan.get(key)

            if value is None:
                continue

            return cls.adapt(value)

        return []

    # =============================================================
    # SEQUENCE ADAPTATION
    # =============================================================

    @classmethod
    def _adapt_sequence(
        cls,
        plan: Any,
    ) -> List[Dict[str, Any]]:

        normalized: List[Dict[str, Any]] = []

        for item in plan:

            # A nested plan.
            if cls.is_plan(item):

                normalized.extend(cls.adapt(item))

                continue

            action = cls.adapt_step(item)

            if action is not None:

                normalized.append(action)

        return normalized

    # =============================================================
    # OBJECT ADAPTATION
    # =============================================================

    @classmethod
    def _adapt_object(
        cls,
        plan: Any,
    ) -> List[Dict[str, Any]]:

        # Common object attributes containing steps.
        for attribute in (
            "steps",
            "actions",
            "plan",
            "workflow",
            "tasks",
        ):

            if not hasattr(plan, attribute):
                continue

            try:
                value = getattr(
                    plan,
                    attribute,
                )
            except Exception:
                continue

            if value is None:
                continue

            return cls.adapt(value)

        # Maybe this object itself represents one action.
        action = cls.adapt_step(plan)

        return [action] if action else []

    # =============================================================
    # ACTION DETECTION
    # =============================================================

    @staticmethod
    def _looks_like_action(
        value: Dict[str, Any],
    ) -> bool:

        return any(
            key in value
            for key in (
                "action",
                "skill",
                "tool",
                "command",
                "name",
            )
        )

    # =============================================================
    # OBJECT → DICTIONARY
    # =============================================================

    @classmethod
    def _object_to_dict(
        cls,
        value: Any,
    ) -> Optional[Dict[str, Any]]:

        if value is None:
            return None

        # ---------------------------------------------------------
        # Try explicit serialization methods first.
        # ---------------------------------------------------------

        for method_name in (
            "to_dict",
            "dict",
            "model_dump",
        ):

            method = getattr(
                value,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = method()

                if isinstance(result, dict):
                    return dict(result)

            except Exception:
                pass

        # ---------------------------------------------------------
        # Extract common action fields.
        # ---------------------------------------------------------

        result: Dict[str, Any] = {}

        for attribute in (
            "action",
            "skill",
            "tool",
            "command",
            "name",
        ):

            if not hasattr(value, attribute):
                continue

            try:

                attribute_value = getattr(
                    value,
                    attribute,
                )

            except Exception:
                continue

            if attribute_value is not None:

                result[attribute] = attribute_value

                break

        # ---------------------------------------------------------
        # Extract parameters.
        # ---------------------------------------------------------

        for attribute in (
            "parameters",
            "params",
            "kwargs",
            "arguments",
        ):

            if not hasattr(value, attribute):
                continue

            try:

                attribute_value = getattr(
                    value,
                    attribute,
                )

            except Exception:
                continue

            if isinstance(attribute_value, dict):

                result["parameters"] = dict(attribute_value)

                break

        # ---------------------------------------------------------
        # Common metadata.
        # ---------------------------------------------------------

        for attribute in (
            "id",
            "step_id",
            "description",
            "metadata",
        ):

            if not hasattr(value, attribute):
                continue

            try:

                attribute_value = getattr(
                    value,
                    attribute,
                )

            except Exception:
                continue

            if attribute_value is not None:

                result[attribute] = attribute_value

        return result or None


# =============================================================
# CONVENIENCE FUNCTIONS
# =============================================================


def adapt_plan(
    plan: Any,
) -> List[Dict[str, Any]]:
    """
    Normalize a plan into V5 action dictionaries.
    """

    return PlanAdapter.adapt(plan)


def adapt_step(
    step: Any,
) -> Optional[Dict[str, Any]]:
    """
    Normalize one step into a V5 action dictionary.
    """

    return PlanAdapter.adapt_step(step)


def is_plan(
    value: Any,
) -> bool:
    """
    Check whether a value appears to represent a plan.
    """

    return PlanAdapter.is_plan(value)


# =============================================================
# EXPORTS
# =============================================================

__all__ = [
    "PlanAdapter",
    "adapt_plan",
    "adapt_step",
    "is_plan",
]
