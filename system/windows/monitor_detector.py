"""
Omnix V5
Monitor Detector

Detects all connected monitors.
"""

from __future__ import annotations

import logging

import win32api
import win32con

logger = logging.getLogger(__name__)


class MonitorDetector:
    """
    Detects desktop monitors.
    """

    def __init__(self) -> None:

        self._monitors: dict[int, dict] = {}

    # ---------------------------------------------------------
    # Detection
    # ---------------------------------------------------------

    def detect(self) -> dict[int, dict]:
        """
        Detect connected monitors.
        """

        self._monitors.clear()

        monitors = win32api.EnumDisplayMonitors()

        for index, monitor in enumerate(monitors):

            handle = monitor[0]

            info = win32api.GetMonitorInfo(
                handle,
            )

            left, top, right, bottom = info["Monitor"]

            work_left, work_top, work_right, work_bottom = info["Work"]

            self._monitors[index] = {
                "id": index,
                "handle": handle,
                "device": info["Device"],
                "primary": bool(
                    info["Flags"] & win32con.MONITORINFOF_PRIMARY
                ),
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
                "width": right - left,
                "height": bottom - top,
                "work_left": work_left,
                "work_top": work_top,
                "work_right": work_right,
                "work_bottom": work_bottom,
                "work_width": work_right - work_left,
                "work_height": work_bottom - work_top,
            }

        logger.info(
            "Detected %d monitor(s).",
            len(self._monitors),
        )

        return dict(self._monitors)

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
    # Helpers
    # ---------------------------------------------------------

    def count(self) -> int:

        return len(
            self._monitors,
        )

    def clear(self) -> None:

        self._monitors.clear()

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
            f"MonitorDetector("
            f"{len(self)} monitors)"
        )