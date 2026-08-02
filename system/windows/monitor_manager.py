"""
Omnix V5
Monitor Manager

Provides monitor lookup and window-monitor operations.
"""

from __future__ import annotations

import logging

from system.models.window import Window

from .monitor_detector import MonitorDetector

logger = logging.getLogger(__name__)


class MonitorManager:
    """
    High-level monitor operations.
    """

    def __init__(self) -> None:

        self._detector = MonitorDetector()

        self._monitors = self._detector.detect()

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self) -> dict[int, dict]:

        self._monitors = self._detector.detect()

        return self._monitors

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def get(
        self,
        monitor_id: int,
    ) -> dict | None:

        return self._monitors.get(
            monitor_id,
        )

    def all(self) -> list[dict]:

        return list(
            self._monitors.values()
        )

    def primary(self) -> dict | None:

        for monitor in self._monitors.values():

            if monitor["primary"]:
                return monitor

        return None

    # ---------------------------------------------------------
    # Window
    # ---------------------------------------------------------

    def monitor_of(
        self,
        window: Window,
    ) -> dict | None:
        """
        Returns the monitor containing
        the center of a window.
        """

        x, y = window.center

        for monitor in self._monitors.values():

            if (
                monitor["left"]
                <= x
                <= monitor["right"]
                and
                monitor["top"]
                <= y
                <= monitor["bottom"]
            ):

                return monitor

        return None

    # ---------------------------------------------------------
    # Point
    # ---------------------------------------------------------

    def monitor_at(
        self,
        x: int,
        y: int,
    ) -> dict | None:

        for monitor in self._monitors.values():

            if (
                monitor["left"]
                <= x
                <= monitor["right"]
                and
                monitor["top"]
                <= y
                <= monitor["bottom"]
            ):

                return monitor

        return None

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def exists(
        self,
        monitor_id: int,
    ) -> bool:

        return monitor_id in self._monitors

    def count(self) -> int:

        return len(
            self._monitors,
        )

    def clear(self) -> None:

        self._monitors.clear()

    def statistics(self) -> dict:

        return {
            "total": len(self._monitors),
            "primary": (
                self.primary()["id"]
                if self.primary()
                else None
            ),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __len__(self) -> int:

        return len(
            self._monitors,
        )

    def __iter__(self):

        return iter(
            self._monitors.values(),
        )

    def __repr__(self) -> str:

        return (
            f"MonitorManager("
            f"{len(self)} monitors)"
        )