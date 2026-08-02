"""
Omnix V5
Window Tracker

Tracks runtime changes to desktop windows.
"""

from __future__ import annotations

import logging
from typing import Callable

from system.models.window import Window

logger = logging.getLogger(__name__)


class WindowTracker:
    """
    Tracks changes in desktop windows.

    Detects:
        • Window opened
        • Window closed
        • Focus changed
        • Title changed
        • Geometry changed
    """

    def __init__(self) -> None:

        self._windows: dict[int, Window] = {}

        self._created_callbacks: list[
            Callable[[Window], None]
        ] = []

        self._closed_callbacks: list[
            Callable[[Window], None]
        ] = []

        self._focus_callbacks: list[
            Callable[[Window], None]
        ] = []

        self._title_callbacks: list[
            Callable[[Window], None]
        ] = []

        self._geometry_callbacks: list[
            Callable[[Window], None]
        ] = []

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update(
        self,
        windows: dict[int, Window],
    ) -> None:

        previous = self._windows

        previous_handles = set(previous)

        current_handles = set(windows)

        # -----------------------------
        # Created
        # -----------------------------

        for handle in current_handles - previous_handles:

            window = windows[handle]

            logger.info(
                "Window created: %s",
                window.title,
            )

            for callback in self._created_callbacks:
                callback(window)

        # -----------------------------
        # Closed
        # -----------------------------

        for handle in previous_handles - current_handles:

            window = previous[handle]

            logger.info(
                "Window closed: %s",
                window.title,
            )

            for callback in self._closed_callbacks:
                callback(window)

        # -----------------------------
        # Existing windows
        # -----------------------------

        for handle in current_handles & previous_handles:

            current = windows[handle]

            old = previous[handle]

            # Focus changed

            if current.focused != old.focused:

                if current.focused:

                    logger.info(
                        "Focus changed: %s",
                        current.title,
                    )

                    for callback in self._focus_callbacks:
                        callback(current)

            # Title changed

            if current.title != old.title:

                logger.info(
                    "Title changed: %s -> %s",
                    old.title,
                    current.title,
                )

                for callback in self._title_callbacks:
                    callback(current)

            # Geometry changed

            if (
                current.rectangle
                != old.rectangle
            ):

                logger.debug(
                    "Geometry changed: %s",
                    current.title,
                )

                for callback in self._geometry_callbacks:
                    callback(current)

        self._windows = dict(windows)

    # ---------------------------------------------------------
    # Registration
    # ---------------------------------------------------------

    def on_created(
        self,
        callback: Callable[[Window], None],
    ) -> None:

        self._created_callbacks.append(
            callback,
        )

    def on_closed(
        self,
        callback: Callable[[Window], None],
    ) -> None:

        self._closed_callbacks.append(
            callback,
        )

    def on_focus_changed(
        self,
        callback: Callable[[Window], None],
    ) -> None:

        self._focus_callbacks.append(
            callback,
        )

    def on_title_changed(
        self,
        callback: Callable[[Window], None],
    ) -> None:

        self._title_callbacks.append(
            callback,
        )

    def on_geometry_changed(
        self,
        callback: Callable[[Window], None],
    ) -> None:

        self._geometry_callbacks.append(
            callback,
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def clear(self) -> None:

        self._windows.clear()

    def windows(self) -> dict[int, Window]:

        return dict(self._windows)

    def statistics(self) -> dict:

        return {
            "tracked": len(
                self._windows,
            ),
        }

    def __len__(self) -> int:

        return len(self._windows)

    def __repr__(self) -> str:

        return (
            f"WindowTracker("
            f"{len(self)} windows)"
        )