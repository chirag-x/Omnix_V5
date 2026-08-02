"""
Omnix V5
Action History

Stores completed automation actions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ActionHistory:
    """
    Stores executed automation actions.

    Each record contains the executed action,
    success status, timestamp, and optional
    execution result.
    """

    def __init__(
        self,
        max_entries: int = 1000,
    ) -> None:

        self._history: list[dict[str, Any]] = []

        self._max_entries = max_entries

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
    # Recording
    # ---------------------------------------------------------

    def record(
        self,
        action: dict[str, Any],
        *,
        successful: bool,
        result: Any = None,
        error: str | None = None,
    ) -> None:

        if not self._enabled:
            return

        entry = {
            "timestamp": datetime.utcnow(),
            "action": action,
            "successful": successful,
            "result": result,
            "error": error,
        }

        self._history.append(
            entry,
        )

        if len(self._history) > self._max_entries:

            self._history.pop(0)

    # ---------------------------------------------------------
    # Access
    # ---------------------------------------------------------

    @property
    def entries(
        self,
    ) -> list[dict[str, Any]]:

        return list(
            self._history,
        )

    @property
    def last(
        self,
    ) -> dict[str, Any] | None:

        if not self._history:
            return None

        return self._history[-1]

    def clear(
        self,
    ) -> None:

        self._history.clear()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def size(
        self,
    ) -> int:

        return len(
            self._history,
        )

    @property
    def is_empty(
        self,
    ) -> bool:

        return not self._history

    def statistics(
        self,
    ) -> dict:

        successful = sum(
            1
            for entry in self._history
            if entry["successful"]
        )

        failed = self.size - successful

        return {
            "enabled": self._enabled,
            "entries": self.size,
            "successful": successful,
            "failed": failed,
            "max_entries": self._max_entries,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __len__(
        self,
    ) -> int:

        return self.size

    def __iter__(
        self,
    ):

        return iter(
            self._history,
        )

    def __repr__(
        self,
    ) -> str:

        return (
            "ActionHistory("
            f"entries={self.size}, "
            f"max_entries={self._max_entries}, "
            f"enabled={self._enabled})"
        )