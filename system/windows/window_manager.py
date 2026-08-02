"""
Omnix V5
Window Manager

High-level interface for desktop window management.
"""

from __future__ import annotations

import logging

from system.models.window import Window

from .focus_manager import FocusManager
from .monitor_manager import MonitorManager
from .window_detector import WindowDetector
from .window_finder import WindowFinder
from .window_state import WindowStateController
from .window_tracker import WindowTracker

logger = logging.getLogger(__name__)


class WindowManager:
    """
    Public API for the Windows subsystem.

    Coordinates:

        • Window detection
        • Window searching
        • Window state control
        • Window tracking
        • Focus management
        • Monitor management
    """

    def __init__(
        self,
        controller=None,
        detector=None,
        tracker=None,
        state=None,
        focus=None,
        monitors=None,
    ):

        self._controller = controller

        self._detector = detector or WindowDetector()

        self._tracker = tracker or WindowTracker()

        self._state = state or WindowStateController()

        self._focus = focus or FocusManager()

        self._monitors = monitors or MonitorManager()

        self._windows: dict[int, Window] = {}

        self._finder = WindowFinder(
            self._windows,
        )

        self._initialized = False

    # ---------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------

    @property
    def initialized(self) -> bool:

        return self._initialized

    def initialize(self) -> None:

        if self._initialized:
            return

        logger.info("Initializing WindowManager...")

        self.refresh()

        self._initialized = True

        logger.info("WindowManager initialized.")

    def shutdown(self) -> None:

        logger.info("Shutting down WindowManager...")

        self._tracker.clear()

        self._windows.clear()

        self._initialized = False

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self) -> dict[int, Window]:

        self._windows = self._detector.detect()

        self._finder = WindowFinder(
            self._windows,
        )

        self._tracker.update(
            self._windows,
        )

        self._monitors.refresh()

        return self._windows

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def count(self) -> int:

        return len(
            self._windows,
        )

    @property
    def foreground(self) -> Window | None:

        handle = self._focus.foreground_handle()

        if handle is None:
            return None

        return self._finder.by_handle(
            handle,
        )

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def get(
        self,
        handle: int,
    ) -> Window | None:

        return self._finder.by_handle(
            handle,
        )

    def all(
        self,
    ) -> list[Window]:

        return self._finder.all()

    def exists(
        self,
        handle: int,
    ) -> bool:

        return self._finder.exists(
            handle,
        )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def by_title(
        self,
        title: str,
    ) -> list[Window]:

        return self._finder.by_title(title)

    def by_process(
        self,
        process_id: int,
    ) -> list[Window]:

        return self._finder.by_process(process_id)

    def by_process_name(
        self,
        name: str,
    ) -> list[Window]:

        return self._finder.by_process_name(name)

    def by_application(
        self,
        application: str,
    ) -> list[Window]:

        return self._finder.by_application(application)

    def visible(
        self,
    ) -> list[Window]:

        return self._finder.visible()

    def minimized(
        self,
    ) -> list[Window]:

        return self._finder.minimized()

    def maximized(
        self,
    ) -> list[Window]:

        return self._finder.maximized()

    # ---------------------------------------------------------
    # Window State
    # ---------------------------------------------------------

    def focus(
        self,
        window: Window,
    ) -> bool:

        return self._state.focus(window)

    def minimize(
        self,
        window: Window,
    ) -> bool:

        return self._state.minimize(window)

    def maximize(
        self,
        window: Window,
    ) -> bool:

        return self._state.maximize(window)

    def restore(
        self,
        window: Window,
    ) -> bool:

        return self._state.restore(window)

    def close(
        self,
        window: Window,
    ) -> bool:

        return self._state.close(window)

    def hide(
        self,
        window: Window,
    ) -> bool:

        return self._state.hide(window)

    def show(
        self,
        window: Window,
    ) -> bool:

        return self._state.show(window)

    def move(
        self,
        window: Window,
        left: int,
        top: int,
    ) -> bool:

        return self._state.move(
            window,
            left,
            top,
        )

    def resize(
        self,
        window: Window,
        width: int,
        height: int,
    ) -> bool:

        return self._state.resize(
            window,
            width,
            height,
        )

    def set_geometry(
        self,
        window: Window,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> bool:

        return self._state.set_geometry(
            window,
            left,
            top,
            width,
            height,
        )

    # ---------------------------------------------------------
    # Focus
    # ---------------------------------------------------------

    def is_focused(
        self,
        window: Window,
    ) -> bool:

        return self._focus.is_focused(
            window,
        )

    def wait_for_focus(
        self,
        window: Window,
        timeout: float = 5.0,
    ) -> bool:

        return self._focus.wait_for_focus(
            window,
            timeout,
        )

    # ---------------------------------------------------------
    # Monitor
    # ---------------------------------------------------------

    @property
    def monitors(
        self,
    ) -> MonitorManager:

        return self._monitors

    def monitor_of(
        self,
        window: Window,
    ):

        return self._monitors.monitor_of(
            window,
        )

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def on_window_created(
        self,
        callback,
    ) -> None:

        self._tracker.on_created(
            callback,
        )

    def on_window_closed(
        self,
        callback,
    ) -> None:

        self._tracker.on_closed(
            callback,
        )

    def on_focus_changed(
        self,
        callback,
    ) -> None:

        self._tracker.on_focus_changed(
            callback,
        )

    def on_title_changed(
        self,
        callback,
    ) -> None:

        self._tracker.on_title_changed(
            callback,
        )

    def on_geometry_changed(
        self,
        callback,
    ) -> None:

        self._tracker.on_geometry_changed(
            callback,
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "windows": self.count,
            "visible": len(self.visible()),
            "minimized": len(self.minimized()),
            "maximized": len(self.maximized()),
            "foreground": (self.foreground.title if self.foreground else None),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __contains__(
        self,
        handle: int,
    ) -> bool:

        return self.exists(
            handle,
        )

    def __len__(
        self,
    ) -> int:

        return self.count

    def __iter__(
        self,
    ):

        return iter(self._windows.values())

    def __repr__(
        self,
    ) -> str:

        return f"WindowManager(" f"{self.count} windows)"
