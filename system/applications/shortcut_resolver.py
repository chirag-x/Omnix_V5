"""
Omnix V5
Shortcut Resolver

Resolves Windows shortcut (.lnk) files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

try:
    import win32com.client
except ImportError:
    win32com = None

logger = logging.getLogger(__name__)


class ShortcutResolver:
    """
    Resolves Windows shortcut (.lnk) files.
    """

    START_MENU_PATHS = (
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
        Path.home() / r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
    )

    DESKTOP_PATHS = (
        Path(r"C:\Users\Public\Desktop"),
        Path.home() / "Desktop",
    )

    def __init__(self) -> None:
        self._shell = None

        if win32com:
            self._shell = win32com.client.Dispatch("WScript.Shell")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def resolve_start_menu(self) -> list[dict]:
        """Resolve all Start Menu shortcuts."""

        return self._scan_locations(self.START_MENU_PATHS)

    def resolve_desktop(self) -> list[dict]:
        """Resolve all Desktop shortcuts."""

        return self._scan_locations(self.DESKTOP_PATHS)

    def resolve_file(self, shortcut: Path) -> dict | None:
        """
        Resolve one shortcut file.

        Returns a dictionary describing the shortcut.
        """

        if self._shell is None:
            return None

        try:
            link = self._shell.CreateShortcut(str(shortcut))

            return {
                "name": shortcut.stem,
                "shortcut": shortcut,
                "target": Path(link.Targetpath) if link.Targetpath else None,
                "arguments": link.Arguments,
                "working_directory": link.WorkingDirectory,
                "icon": link.IconLocation,
            }

        except Exception:
            logger.exception("Unable to resolve shortcut: %s", shortcut)
            return None

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _scan_locations(
        self,
        locations: tuple[Path, ...],
    ) -> list[dict]:

        shortcuts = []

        for location in locations:

            if not location.exists():
                continue

            for file in self._iter_shortcuts(location):

                info = self.resolve_file(file)

                if info:
                    shortcuts.append(info)

        logger.info("Resolved %d shortcuts.", len(shortcuts))

        return shortcuts

    def _iter_shortcuts(
        self,
        folder: Path,
    ) -> Iterator[Path]:

        yield from folder.rglob("*.lnk")