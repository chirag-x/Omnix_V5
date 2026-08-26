"""
Omnix V5 - Legacy Compatibility Adapter

Provides a small compatibility layer for interacting with
older Omnix components that may expose different method names,
result formats, or object interfaces.

This module does NOT execute specific automation actions.
Action normalization belongs in action_adapter.py.

This module does NOT normalize plans.
Plan normalization belongs in plan_adapter.py.
"""

from __future__ import annotations

import asyncio
import inspect

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Optional

# ============================================================================
# COMMON LEGACY METHOD ALIASES
# ============================================================================

METHOD_ALIASES: Dict[str, tuple[str, ...]] = {
    "plan": (
        "plan",
        "create_plan",
        "build_plan",
        "generate_plan",
        "make_plan",
    ),
    "execute": (
        "execute",
        "run",
        "execute_plan",
        "execute_task",
        "run_task",
    ),
    "cancel": (
        "cancel",
        "stop",
        "abort",
        "terminate",
    ),
    "status": (
        "status",
        "get_status",
        "health",
        "health_status",
    ),
    "start": (
        "start",
        "initialize",
        "init",
        "run",
    ),
    "shutdown": (
        "shutdown",
        "stop",
        "close",
        "terminate",
    ),
}


# ============================================================================
# LEGACY ADAPTER
# ============================================================================


class LegacyAdapter:
    """
    Generic compatibility helper for old and new Omnix APIs.

    It can:

    - find compatible methods
    - call methods using common aliases
    - resolve synchronous or asynchronous results
    - convert common result objects into dictionaries
    - safely inspect objects with mixed V4/V5 interfaces
    """

    # ========================================================================
    # METHOD DISCOVERY
    # ========================================================================

    @classmethod
    def find_method(
        cls,
        target: Any,
        capability: str,
    ) -> Optional[Any]:
        """
        Find the first callable method matching a capability.

        Example:

            LegacyAdapter.find_method(
                planner,
                "plan",
            )

        will check:

            plan()
            create_plan()
            build_plan()
            generate_plan()
            make_plan()
        """

        if target is None:
            return None

        capability = str(capability).strip().lower()

        if not capability:
            return None

        candidates = METHOD_ALIASES.get(
            capability,
            (capability,),
        )

        for method_name in candidates:

            method = getattr(
                target,
                method_name,
                None,
            )

            if callable(method):
                return method

        return None

    @classmethod
    def has_capability(
        cls,
        target: Any,
        capability: str,
    ) -> bool:
        """
        Return True if the target supports a capability.
        """

        return (
            cls.find_method(
                target,
                capability,
            )
            is not None
        )

    # ========================================================================
    # SAFE METHOD CALLING
    # ========================================================================

    @classmethod
    def call(
        cls,
        target: Any,
        capability: str,
        *args: Any,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        """
        Find and call a compatible method.

        Returns `default` when no compatible method exists.

        Exceptions raised by the target method are not hidden.
        """

        method = cls.find_method(
            target,
            capability,
        )

        if method is None:
            return default

        result = method(
            *args,
            **kwargs,
        )

        return cls.resolve_result(result)

    # ========================================================================
    # RESULT RESOLUTION
    # ========================================================================

    @staticmethod
    def resolve_result(
        result: Any,
    ) -> Any:
        """
        Resolve awaitable results.

        If called outside an active event loop, the coroutine
        is executed synchronously.

        If an event loop is already running, the awaitable is
        returned unchanged so the caller can await it.
        """

        if not inspect.isawaitable(result):
            return result

        try:
            asyncio.get_running_loop()

        except RuntimeError:
            return asyncio.run(result)

        return result

    # ========================================================================
    # SAFE ATTRIBUTE ACCESS
    # ========================================================================

    @staticmethod
    def get_attribute(
        target: Any,
        names: Iterable[str],
        default: Any = None,
    ) -> Any:
        """
        Return the first existing non-None attribute.

        Example:

            get_attribute(
                result,
                ("output", "value", "result"),
            )
        """

        if target is None:
            return default

        for name in names:

            try:
                value = getattr(
                    target,
                    name,
                )

            except Exception:
                continue

            if value is not None:
                return value

        return default

    @classmethod
    def get_value(
        cls,
        target: Any,
        names: Iterable[str],
        default: Any = None,
    ) -> Any:
        """
        Get a value from either a dictionary or object.
        """

        if target is None:
            return default

        if isinstance(target, dict):

            for name in names:

                if name in target and target[name] is not None:

                    return target[name]

            return default

        return cls.get_attribute(
            target,
            names,
            default,
        )

    # ========================================================================
    # RESULT NORMALIZATION
    # ========================================================================

    @classmethod
    def to_dict(
        cls,
        value: Any,
    ) -> Dict[str, Any]:
        """
        Convert common result objects to dictionaries.

        This is intentionally conservative. Unknown objects
        are preserved under the 'value' key instead of being
        aggressively introspected.
        """

        if value is None:
            return {}

        if isinstance(value, dict):
            return dict(value)

        if is_dataclass(value):

            try:
                return asdict(value)
            except Exception:
                pass

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
                continue

        return {
            "value": value,
        }

    @classmethod
    def normalize_result(
        cls,
        result: Any,
    ) -> Dict[str, Any]:
        """
        Normalize common V4/V5 result formats.

        Output always contains:

            success
            output
            error
            raw
        """

        resolved = cls.resolve_result(result)

        # If still awaitable, do not consume it here.
        if inspect.isawaitable(resolved):

            return {
                "success": None,
                "output": resolved,
                "error": None,
                "raw": resolved,
            }

        # Boolean result.
        if isinstance(resolved, bool):

            return {
                "success": resolved,
                "output": None,
                "error": None if resolved else "Operation failed.",
                "raw": resolved,
            }

        # Legacy string result.
        if isinstance(resolved, str):

            lowered = resolved.strip().lower()

            if lowered in {
                "success",
                "completed",
                "complete",
                "done",
                "ok",
            }:

                return {
                    "success": True,
                    "output": resolved,
                    "error": None,
                    "raw": resolved,
                }

            if lowered in {
                "error",
                "failed",
                "failure",
            }:

                return {
                    "success": False,
                    "output": None,
                    "error": resolved,
                    "raw": resolved,
                }

            return {
                "success": True,
                "output": resolved,
                "error": None,
                "raw": resolved,
            }

        data = cls.to_dict(resolved)

        success = cls.get_value(
            data,
            (
                "success",
                "ok",
            ),
            default=None,
        )

        if success is None:

            status = cls.get_value(
                data,
                (
                    "status",
                    "state",
                ),
                default=None,
            )

            if status is not None:

                status_text = str(status).strip().lower()

                if status_text in {
                    "success",
                    "completed",
                    "complete",
                    "done",
                    "ok",
                }:

                    success = True

                elif status_text in {
                    "error",
                    "failed",
                    "failure",
                    "cancelled",
                    "canceled",
                }:

                    success = False

        if success is None:
            success = True

        output = cls.get_value(
            data,
            (
                "output",
                "value",
                "result",
                "data",
            ),
            default=None,
        )

        error = cls.get_value(
            data,
            (
                "error",
                "message",
                "reason",
            ),
            default=None,
        )

        return {
            "success": bool(success),
            "output": output,
            "error": (str(error) if error is not None else None),
            "raw": resolved,
        }

    # ========================================================================
    # INTERFACE INSPECTION
    # ========================================================================

    @classmethod
    def describe(
        cls,
        target: Any,
    ) -> Dict[str, Any]:
        """
        Describe which standard Omnix capabilities an object supports.
        """

        if target is None:

            return {
                "available": False,
                "capabilities": {},
            }

        capabilities = {}

        for capability in METHOD_ALIASES:

            capabilities[capability] = cls.has_capability(
                target,
                capability,
            )

        return {
            "available": True,
            "type": (f"{type(target).__module__}." f"{type(target).__name__}"),
            "capabilities": capabilities,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def find_compatible_method(
    target: Any,
    capability: str,
) -> Optional[Any]:

    return LegacyAdapter.find_method(
        target,
        capability,
    )


def call_compatible(
    target: Any,
    capability: str,
    *args: Any,
    default: Any = None,
    **kwargs: Any,
) -> Any:

    return LegacyAdapter.call(
        target,
        capability,
        *args,
        default=default,
        **kwargs,
    )


def normalize_legacy_result(
    result: Any,
) -> Dict[str, Any]:

    return LegacyAdapter.normalize_result(result)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "METHOD_ALIASES",
    "LegacyAdapter",
    "find_compatible_method",
    "call_compatible",
    "normalize_legacy_result",
]
