"""
Omnix V5
Debug Tools

Developer debugging utilities.
"""

from __future__ import annotations

import logging
import traceback

from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class DebugTools:
    """
    Provides debugging utilities for Omnix.
    """

    def __init__(
        self,
    ) -> None:

        self._objects: dict[str, Any] = {}

        self._errors: list[dict] = []

    # ---------------------------------------------------------
    # Object Registration
    # ---------------------------------------------------------

    def register(
        self,
        name: str,
        obj: Any,
    ) -> None:

        self._objects[name] = obj

    def unregister(
        self,
        name: str,
    ) -> None:

        self._objects.pop(
            name,
            None,
        )

    def has_object(
        self,
        name: str,
    ) -> bool:

        return name in self._objects

    # ---------------------------------------------------------
    # Inspection
    # ---------------------------------------------------------

    def inspect(
        self,
        name: str,
    ) -> dict | None:

        obj = self._objects.get(
            name,
        )

        if obj is None:

            return None

        result = {
            "name": name,
            "type": type(obj).__name__,
        }

        try:

            result["repr"] = repr(obj)

        except Exception:

            result["repr"] = "unavailable"

        if hasattr(
            obj,
            "statistics",
        ):

            try:

                result["statistics"] = obj.statistics()

            except Exception as exc:

                result["statistics_error"] = str(exc)

        return result

    def inspect_all(
        self,
    ) -> dict:

        output = {}

        for name in self._objects:

            output[name] = self.inspect(
                name,
            )

        return output

    # ---------------------------------------------------------
    # Error Tracking
    # ---------------------------------------------------------

    def capture_error(
        self,
        error: Exception,
        context: str = "",
    ) -> None:

        self._errors.append(
            {
                "time": datetime.utcnow().isoformat(),
                "context": context,
                "error": str(error),
                "type": type(error).__name__,
                "traceback": traceback.format_exc(),
            }
        )

    def errors(
        self,
    ) -> list[dict]:

        return self._errors.copy()

    def latest_error(
        self,
    ) -> dict | None:

        if not self._errors:

            return None

        return self._errors[-1]

    def clear_errors(
        self,
    ) -> None:

        self._errors.clear()

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    def dump(
        self,
    ) -> dict:

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "objects": self.inspect_all(),
            "errors": self.errors(),
        }

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "objects": len(self._objects),
            "errors": len(self._errors),
        }

    def __repr__(
        self,
    ) -> str:

        return (
            "DebugTools("
            f"objects={len(self._objects)}, "
            f"errors={len(self._errors)})"
        )
