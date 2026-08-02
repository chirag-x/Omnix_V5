"""
Omnix V5
Path Utilities

Central path management.
"""

from __future__ import annotations

from pathlib import Path


from .constants import (
    SYSTEM_FOLDER,
    CONFIG_FOLDER,
    LOG_FOLDER,
    MEMORY_FOLDER,
    ASSETS_FOLDER,
)


class PathManager:
    """
    Manages Omnix paths.
    """

    def __init__(
        self,
        root: str | Path | None = None,
    ) -> None:

        self._root = Path(root or Path.cwd())

    # ---------------------------------------------------------
    # Root
    # ---------------------------------------------------------

    @property
    def root(
        self,
    ) -> Path:

        return self._root

    # ---------------------------------------------------------
    # Main Folders
    # ---------------------------------------------------------

    def system(
        self,
    ) -> Path:

        return self._root / SYSTEM_FOLDER

    def config(
        self,
    ) -> Path:

        return self._root / CONFIG_FOLDER

    def logs(
        self,
    ) -> Path:

        return self._root / LOG_FOLDER

    def memory(
        self,
    ) -> Path:

        return self._root / MEMORY_FOLDER

    def assets(
        self,
    ) -> Path:

        return self._root / ASSETS_FOLDER

    # ---------------------------------------------------------
    # Join
    # ---------------------------------------------------------

    def join(
        self,
        *parts: str,
    ) -> Path:
        """
        Safely join paths.
        """

        path = self._root

        for part in parts:

            path /= part

        return path

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def ensure(
        self,
        path: Path,
    ) -> Path:
        """
        Create directory if missing.
        """

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    def ensure_structure(
        self,
    ) -> None:
        """
        Create Omnix folders.
        """

        folders = [
            self.system(),
            self.config(),
            self.logs(),
            self.memory(),
            self.assets(),
        ]

        for folder in folders:

            self.ensure(
                folder,
            )

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "root": str(self._root),
            "folders": [
                str(self.system()),
                str(self.config()),
                str(self.logs()),
                str(self.memory()),
                str(self.assets()),
            ],
        }

    def __repr__(
        self,
    ) -> str:

        return "PathManager(" f"root={self._root})"
