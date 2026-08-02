"""
Omnix V5
Window Detector

Detects top-level desktop windows.
"""

from __future__ import annotations

import logging
from datetime import datetime

import win32gui
import win32process

SW_SHOWMINIMIZED = 7

from system.models.window import Window

logger = logging.getLogger(__name__)


class WindowDetector:
    """
    Detects desktop windows.

    Responsibilities
    ----------------
    • Enumerate top-level windows
    • Read window metadata
    • Convert Win32 windows into Window models

    This class DOES NOT:

        • Move windows
        • Resize windows
        • Focus windows
        • Monitor changes
    """

    def __init__(self) -> None:

        self._windows: dict[int, Window] = {}

        self._last_scan: datetime | None = None

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def last_scan(self) -> datetime | None:

        return self._last_scan

    @property
    def count(self) -> int:

        return len(self._windows)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def detect(self) -> dict[int, Window]:
        """
        Detect all top-level windows.
        """

        logger.info("Scanning desktop windows...")

        self._windows.clear()

        win32gui.EnumWindows(
            self._enum_callback,
            None,
        )

        self._last_scan = datetime.now()

        logger.info(
            "Detected %d windows.",
            len(self._windows),
        )

        return dict(self._windows)

    def refresh(self) -> dict[int, Window]:

        return self.detect()

    def get_windows(self) -> dict[int, Window]:

        return dict(self._windows)

    def get_window(
        self,
        hwnd: int,
    ) -> Window | None:

        return self._windows.get(hwnd)

    def clear(self) -> None:

        self._windows.clear()

        self._last_scan = None

    # ---------------------------------------------------------
    # Enumeration
    # ---------------------------------------------------------

    def _enum_callback(
        self,
        hwnd: int,
        _,
    ) -> bool:

        try:

            window = self._build_window(hwnd)

            if window is not None:

                self._windows[hwnd] = window

        except Exception:

            logger.exception(
                "Failed detecting window %s",
                hwnd,
            )

        return True

    # ---------------------------------------------------------
    # Builder
    # ---------------------------------------------------------

    def _build_window(
        self,
        hwnd: int,
    ) -> Window | None:
        """
        Convert a Win32 window into a Window model.
        """

        # Skip invalid handles
        if not win32gui.IsWindow(hwnd):
            return None

        title = win32gui.GetWindowText(hwnd).strip()

        # Skip untitled windows
        if not title:
            return None

        try:
            thread_id, process_id = win32process.GetWindowThreadProcessId(
                hwnd,
            )

            left, top, right, bottom = win32gui.GetWindowRect(
                hwnd,
            )

            width = max(
                0,
                right - left,
            )

            height = max(
                0,
                bottom - top,
            )

            visible = bool(win32gui.IsWindowVisible(hwnd))

            enabled = bool(win32gui.IsWindowEnabled(hwnd))

            placement = win32gui.GetWindowPlacement(hwnd)

            minimized = placement[1] == SW_SHOWMINIMIZED

            maximized = placement[1] == 3

            focused = hwnd == win32gui.GetForegroundWindow()

            class_name = win32gui.GetClassName(
                hwnd,
            )

            window = Window(
                handle=hwnd,
                title=title,
                process_id=process_id,
                left=left,
                top=top,
                width=width,
                height=height,
                visible=visible,
                enabled=enabled,
                minimized=minimized,
                maximized=maximized,
                focused=focused,
                class_name=class_name,
            )

            # Optional metadata
            if hasattr(window, "thread_id"):
                window.thread_id = thread_id

            return window

        except Exception:

            logger.exception(
                "Failed building window %s",
                hwnd,
            )

            return None

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def exists(
        self,
        hwnd: int,
    ) -> bool:

        return hwnd in self._windows

    def handles(self) -> list[int]:

        return list(self._windows.keys())

    def __contains__(
        self,
        hwnd: int,
    ) -> bool:

        return hwnd in self._windows

    def __len__(self) -> int:

        return len(self._windows)

    def __iter__(self):

        return iter(self._windows.values())

    def __repr__(self) -> str:

        return f"WindowDetector(" f"{len(self)} windows)"
