"""
Omnix V5
Window Finder

Provides searching and filtering over detected windows.
"""

from __future__ import annotations

from system.models.window import Window


class WindowFinder:
    """
    Searches Window objects.

    This class never scans Windows itself.
    It only searches an existing collection.
    """

    def __init__(
        self,
        windows: dict[int, Window],
    ) -> None:

        self._windows = windows

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def by_handle(
        self,
        handle: int,
    ) -> Window | None:

        return self._windows.get(handle)

    def exists(
        self,
        handle: int,
    ) -> bool:

        return handle in self._windows

    def all(
        self,
    ) -> list[Window]:

        return list(
            self._windows.values()
        )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def by_title(
        self,
        title: str,
    ) -> list[Window]:

        title = title.lower()

        return [
            window
            for window in self._windows.values()
            if title in window.title.lower()
        ]

    def by_process(
        self,
        process_id: int,
    ) -> list[Window]:

        return [
            window
            for window in self._windows.values()
            if window.process_id == process_id
        ]

    def by_process_name(
        self,
        name: str,
    ) -> list[Window]:

        name = name.lower()

        return [
            window
            for window in self._windows.values()
            if window.process_name
            and name in window.process_name.lower()
        ]

    def by_application(
        self,
        application: str,
    ) -> list[Window]:

        application = application.lower()

        return [
            window
            for window in self._windows.values()
            if window.application
            and application
            in window.application.lower()
        ]

    def by_class(
        self,
        class_name: str,
    ) -> list[Window]:

        class_name = class_name.lower()

        return [
            window
            for window in self._windows.values()
            if window.class_name
            and class_name
            in window.class_name.lower()
        ]

    # ---------------------------------------------------------
    # State Filters
    # ---------------------------------------------------------

    def visible(
        self,
    ) -> list[Window]:

        return [
            window
            for window in self._windows.values()
            if window.visible
        ]

    def hidden(
        self,
    ) -> list[Window]:

        return [
            window
            for window in self._windows.values()
            if not window.visible
        ]

    def focused(
        self,
    ) -> Window | None:

        for window in self._windows.values():

            if window.focused:
                return window

        return None

    def minimized(
        self,
    ) -> list[Window]:

        return [
            window
            for window in self._windows.values()
            if window.minimized
        ]

    def maximized(
        self,
    ) -> list[Window]:

        return [
            window
            for window in self._windows.values()
            if window.maximized
        ]

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def at_position(
        self,
        x: int,
        y: int,
    ) -> Window | None:

        for window in reversed(
            list(self._windows.values())
        ):

            if window.contains(
                x,
                y,
            ):
                return window

        return None

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        windows = list(
            self._windows.values()
        )

        return {
            "total": len(windows),
            "visible": sum(
                w.visible for w in windows
            ),
            "hidden": sum(
                not w.visible for w in windows
            ),
            "minimized": sum(
                w.minimized for w in windows
            ),
            "maximized": sum(
                w.maximized for w in windows
            ),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __len__(
        self,
    ) -> int:

        return len(
            self._windows
        )

    def __contains__(
        self,
        handle: int,
    ) -> bool:

        return handle in self._windows

    def __iter__(
        self,
    ):

        return iter(
            self._windows.values()
        )

    def __repr__(
        self,
    ) -> str:

        return (
            f"WindowFinder("
            f"{len(self)} windows)"
        )