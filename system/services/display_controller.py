"""
Omnix V5
Display Controller

Low-level display and monitor operations.
"""

from __future__ import annotations

import logging

import screeninfo

logger = logging.getLogger(__name__)


class DisplayController:
    """
    Low-level display controller.
    """

    def __init__(
        self,
    ) -> None:

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
    # Monitor Information
    # ---------------------------------------------------------

    def monitors(
        self,
    ) -> list[dict]:

        """
        Return connected displays.
        """

        if not self._enabled:

            return []

        result = []

        try:

            for index, monitor in enumerate(
                screeninfo.get_monitors()
            ):

                result.append(
                    {
                        "id": index,
                        "name": monitor.name,
                        "x": monitor.x,
                        "y": monitor.y,
                        "width": monitor.width,
                        "height": monitor.height,
                        "primary": monitor.is_primary,
                    }
                )

            return result

        except Exception as exc:

            logger.error(
                "Monitor detection failed: %s",
                exc,
            )

            return []


    def primary(
        self,
    ) -> dict | None:

        for monitor in self.monitors():

            if monitor["primary"]:

                return monitor

        return None


    # ---------------------------------------------------------
    # Resolution
    # ---------------------------------------------------------

    def resolution(
        self,
        monitor_id: int = 0,
    ) -> tuple[int, int] | None:

        displays = self.monitors()

        for monitor in displays:

            if monitor["id"] == monitor_id:

                return (
                    monitor["width"],
                    monitor["height"],
                )

        return None


    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {

            "enabled": self._enabled,

            "monitors": len(
                self.monitors()
            ),

        }


    def __repr__(
        self,
    ) -> str:

        return (
            "DisplayController("
            f"enabled={self._enabled})"
        )