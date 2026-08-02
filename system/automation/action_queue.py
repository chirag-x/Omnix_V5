"""
Omnix V5
Action Queue

Queue of pending automation actions.
"""

from __future__ import annotations

from collections import deque
from typing import Any


class ActionQueue:
    """
    FIFO queue for automation actions.

    Stores actions until they are executed by
    the ActionExecutor.
    """

    def __init__(self) -> None:

        self._queue: deque[dict[str, Any]] = deque()

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
    # Queue Operations
    # ---------------------------------------------------------

    def enqueue(
        self,
        action: dict[str, Any],
    ) -> None:

        if not self._enabled:
            return

        self._queue.append(
            action,
        )

    def dequeue(
        self,
    ) -> dict[str, Any] | None:

        if not self._enabled:
            return None

        if not self._queue:
            return None

        return self._queue.popleft()

    def peek(
        self,
    ) -> dict[str, Any] | None:

        if not self._queue:
            return None

        return self._queue[0]

    def clear(
        self,
    ) -> None:

        self._queue.clear()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def is_empty(
        self,
    ) -> bool:

        return (
            len(
                self._queue,
            )
            == 0
        )

    @property
    def size(
        self,
    ) -> int:

        return len(
            self._queue,
        )

    def __len__(
        self,
    ) -> int:

        return len(
            self._queue,
        )

    def __iter__(
        self,
    ):

        return iter(
            self._queue,
        )

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
            "size": len(
                self._queue,
            ),
            "empty": self.is_empty,
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "ActionQueue(" f"size={len(self._queue)}, " f"enabled={self._enabled})"
